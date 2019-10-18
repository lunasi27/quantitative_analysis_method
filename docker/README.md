1, Build new image:
docker build -t stock_web:1.0 .

2, Run docker image:
# -p host_port:continer_port
# -v host_path:continer_path
# 当需要把数据保存在宿主机上时，需要先建立一个docker卷，然后将卷映射到对应的目录上。直接用-v映射/var/lib/mongodb目录会有问题
# docker volume create --driver local --opt type=none --opt device=/root/stock_web/mongo_data --opt o=bind --name=mongo_data
# docker run -d -p 9000:9000 -p 27018:27017 -v mongo_data:/var/lib/mongodb stock_web:1.0
# 如果希望在删除continer的同时删除卷，则在docker run命令后加上--rm参数
# 或者手动docker rm -v <容器名>
# 因为共享容器的创建需要管理员自己记住容器名及作用，所以最好使用容器编排工具来实现这个。
docker run -d -p 9000:9000 -p 27017:27017 stock_web:1.0
docker run -d -p 9000:9000 -p 27017:27017 -v mongo_data:/var/lib/mongodb stock_web:1.0
docker run -it -p 9000:9000 -p 27017:27017 stock_web:1.0 bash
docker exec -it d4467c46609c bash


3， 可以在docker启动时，使用这种方式来保持时间一致
-v /etc/localtime:/etc/localtime

4， 查看端口占用
netstat -ntlp