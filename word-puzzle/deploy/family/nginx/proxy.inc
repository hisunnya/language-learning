# 转给后端时统一设置的头。覆盖掉客户端自己带的值，不让外面的人伪造。
proxy_http_version 1.1;
proxy_set_header Connection "";
proxy_set_header Host $http_host;
proxy_set_header X-Forwarded-Host $http_host;
proxy_set_header X-Forwarded-Proto https;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $remote_addr;
proxy_connect_timeout 10s;
proxy_read_timeout 600s;
proxy_send_timeout 600s;
