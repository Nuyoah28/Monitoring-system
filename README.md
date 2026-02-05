algorithm：python模型训练的代码和python后端的代码

backend：Java后端代码 jdk17 不然的话会报错，有个低版本的依赖

后端配置：（mysql和redis）
Monitoring-system/backend/src/main/resources/application-dev.yml 这个里面有数据库，redis的配置 配置好自己的密码

在后端backend打开，mvn clean install -DskipTests配置后端
mvn spring-boot:run 启动


city_app：安卓端前端代码
在city_app下打开，npm i 安装依赖
下载HBuilderX 在HBuilderX中打开目录/文件夹找到city_app打开即可
找到工具-插件 下载对应的插件 推荐：内置浏览器，内置终端，uniapp编译器 vue2（目前是），vue3，git插件，还有些会自动下载没关系
完成后随便打开文件夹下的一个文件 找到最上方的运行-运行到内置浏览器 即可。



web：网页端前端代码
在前端web下打开，npm i 安装依赖
npm run serve 启动

iot：嵌入式代码


整体运行的时候，先开后段 前端可以选择开 然后开app端