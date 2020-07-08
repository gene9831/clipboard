# 超简单剪切板

`flask` + `vue.js` + `element-ui.js` 实现的超简单局域网剪切板，数据存储在内存中。

## TODO

- [x] 剪切板实时同步
- [x] 文件锁，最多同时一个人编辑
- [x] 显示在线人数
- [x] 同步状态提示
- [ ] 用户注册登录
- [ ] 显示编辑者

## 环境

### 前端

- `vue 2.6.11`
- `vue-clipboard2 0.3.1`
- `element-ui 2.13.2`
- `axios 0.19.2`

### 后端

- `python 3.8`
- `Flask-RESTful 0.3.8`
- `waitress 1.4.4`

## 安装依赖

```shell
pip3 install -r requirements.txt
```

## 使用

```shell
python3 app.py
```

浏览器打开 [http://127.0.0.1:8899](http://127.0.0.1:8899/)

## 截图

![截图](https://s1.ax1x.com/2020/07/09/UeElNV.png)
