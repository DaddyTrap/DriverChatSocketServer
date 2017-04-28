# Driver Chat Protocol

> Version 1

[TOC]

```
{
  "type": "chat"/"sys"
}

```

## 客户端向服务端

### 聊天消息

```
{
  "type": "chat",
  "msg": String,    // 信息
  "to": Integer     // 房号
}
```

### 系统消息

#### 登录

```
{
  "type": "sys",
  "detail": "sign in",
  "driver": {
    "username": String,
    "password": String
  }
}
```

#### 注册

```
{
  "type": "sys",
  "detail": "sign up",
  "driver": {
    "username": String,
    "password": String,
    "name": String,
    "created_at: String,
    "avatar": Blob      // 待定
  }
}
```

#### 更新房间列表

```
{
  "type": "sys",
  "detail": "room list"
}
```

#### 更新房间用户列表信息

```
{
  "type": "sys",
  "detail": "driver list",
  "room": {
    "rid": Integer
  }
}
```

## 服务端向客户端

### 聊天消息

```
{
  "type": "chat",
  "msg": String,    // 司机发来的信息
  "from": Integer,  // 来自的司机的id
  "to": Integer     // 房号
}
```

### 系统消息

#### 登录

```
{
  "type": "sys",
  "detail": "sign in",
  "status": true/false, // 表示登录是否成功
  "msg": String,        // 如果登录失败，则有失败信息
  "driver": {
    "did": Integer,
    "name": String,
    "badget": String,
    "created_at: String,
    "avatar": Blob      // 待定
  }
}
```

#### 注册

```
{
  "type": "sys",
  "detail": "sign up",
  "status": true/false, // 表示注册是否成功
  "msg": String,        // 如果注册失败，则有失败信息
  "did": Integer
}
```

#### 更新房间列表

```
{
  "type": "sys",
  "detail": "room list",
  "rooms": [{
    "rid": Integer,
    "name": String,
    "direction": String,
    "activeness": Integer,
    "created_at": String
  }, ...]
}
```

#### 更新房间用户列表信息

```
{
  "type": "sys",
  "detail": "driver list",
  "room": {
    "rid": Integer
  },
  "drivers": [{
    "did": Integer,
    "nickname": String,
    "badge": String,
    "avatar": BLOB    // 未定，可能弃用
  }, ...]
}
```

## 文件

```
{
  "type": "file",
  "format": "raw/image",
  "length": Integer,
  "from": Integer,
  "to": Integer
}
```
