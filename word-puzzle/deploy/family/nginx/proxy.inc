# 转给后端时统一设置的头。覆盖掉客户端自己带的值，不让外面的人伪造。
proxy_http_version 1.1;
proxy_set_header Connection "";
proxy_set_header Host $http_host;
proxy_set_header X-Forwarded-Host $http_host;
proxy_set_header X-Forwarded-Proto https;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $remote_addr;
# 访问记录用：把「上一跳（Tailscale Funnel）告诉我们的」原样存到专用的头里。这几个头 nginx 每次都覆盖，
# 外面的人写不进来；后端取其中最后一个有效地址当客户端 IP，全部转发头也存下来备查。
proxy_set_header X-Wp-Edge-Xff $http_x_forwarded_for;
proxy_set_header X-Wp-Edge-Real-Ip $http_x_real_ip;
proxy_set_header X-Wp-Edge-Forwarded $http_forwarded;
proxy_set_header X-Wp-Edge-Tailscale $http_tailscale_user_login;
proxy_connect_timeout 10s;
proxy_read_timeout 600s;
proxy_send_timeout 600s;
