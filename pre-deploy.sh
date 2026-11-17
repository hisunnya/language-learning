#!/usr/bin/env bash
# 部署前保险：在 PVE 宿主机上、部署之前运行一次。
#   1. 给学生版容器打一个快照（回滚容器里的代码和系统）
#   2. 用 SQLite 的 backup 接口给数据库做一份一致的备份（回滚数据；不能直接 cp，库是 WAL 模式）
#   3. 记下当前提交和快照名，打印出出问题时该敲的回滚命令
# 需要 deploy.local.env 里有 LEXICA_CTID=容器编号（和别的私有值一样，不进仓库）。
#   sudo bash pre-deploy.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$REPO_DIR/deploy.local.env"
[[ -f "$ENV_FILE" ]] || { echo "没有 $ENV_FILE" >&2; exit 1; }
CTID=""
while IFS='=' read -r key value; do
  [[ "$key" == "LEXICA_CTID" ]] && CTID="${value//\"/}"
done < "$ENV_FILE"
[[ "$CTID" =~ ^[0-9]+$ ]] || { echo "deploy.local.env 里要有 LEXICA_CTID=容器编号" >&2; exit 1; }
command -v pct >/dev/null || { echo "要在 PVE 宿主机上运行（找不到 pct）" >&2; exit 1; }

STAMP="$(date +%Y%m%d_%H%M%S)"
SNAP="pre_deploy_$STAMP"
COMMIT="$(git -C "$REPO_DIR" rev-parse --short HEAD)"
NOTE="/root/pre-deploy-$STAMP.txt"

echo "==> 1/3 容器快照 $SNAP"
if ! pct snapshot "$CTID" "$SNAP" --description "before deploy, repo at $COMMIT"; then
  echo "快照失败（存储不支持快照？）。没有快照就不要继续部署，除非你接受只靠数据库备份回滚。" >&2
  exit 1
fi

echo "==> 2/3 数据库备份"
BACKUP_FILE="/backup/$SNAP.db"
pct exec "$CTID" -- runuser -u wpfamily -- python3 - "$BACKUP_FILE" <<'PY'
import sqlite3, sys
src = sqlite3.connect("/var/lib/word-puzzle-family/app.db", timeout=30)
dst = sqlite3.connect(sys.argv[1])
src.backup(dst)
ok = dst.execute("PRAGMA integrity_check").fetchone()[0]
print("备份完成，完整性检查：", ok, "，schema 版本：", src.execute("PRAGMA user_version").fetchone()[0])
dst.close(); src.close()
if ok != "ok":
    sys.exit("备份没通过完整性检查")
PY

echo "==> 3/3 记录"
cat > "$NOTE" <<NOTE_EOF
部署前状态 $STAMP
  仓库提交      ： $COMMIT
  容器快照      ： $SNAP（容器 $CTID）
  数据库备份    ： 容器里 $BACKUP_FILE
NOTE_EOF
chmod 600 "$NOTE"

cat <<DONE

保险做好了（记录在 $NOTE）。现在可以部署。

出问题时的回滚：
  容器代码 + 数据库：
    pct stop $CTID
    pct rollback $CTID $SNAP
    pct start $CTID
    # 快照不含数据库（它在挂载目录里）；新版本改过库结构，需要把备份放回去：
    pct exec $CTID -- systemctl stop word-puzzle-family
    pct exec $CTID -- bash -c 'rm -f /var/lib/word-puzzle-family/app.db-wal /var/lib/word-puzzle-family/app.db-shm && cp $BACKUP_FILE /var/lib/word-puzzle-family/app.db && chown wpfamily:wpfamily /var/lib/word-puzzle-family/app.db'
    pct exec $CTID -- systemctl start word-puzzle-family
  宿主机（静态站、nginx）：
    cd $REPO_DIR && git checkout $COMMIT && sudo bash deploy-all-*.sh   # 用那个提交里自带的旧脚本
  回滚数据库会丢掉部署之后产生的成绩和访问记录。
DONE
