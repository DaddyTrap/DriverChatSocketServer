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

#### 进入房间

```
{
  "type": "sys",
  "detail": "enter room",
  "rid": Integer
}
```

#### 退出房间

```
{
  "type": "sys",
  "detail": "quit room",
  "rid": Integer
}
```

#### 更新房间用户列表信息

```
{
  "type": "sys",
  "detail": "driver list",
  "rid": Integer
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

#### 进入房间

```
{
  "type": "sys",
  "detail": "enter room",
  "rid": Integer,
  "status": true/false
}
```

#### 退出房间

```
{
  "type": "sys",
  "detail": "quit room",
  "rid": Integer,
  "status": true/false
}
```

#### 更新房间用户列表信息

```
{
  "type": "sys",
  "detail": "driver list",
  "rid": Integer,
  "drivers": [{
    "did": Integer,
    "name": String,
    "badge": String,
    "avatar": String
  }, ...]
}
```

## 文件

```
{
  "type": "file",
  "updown": "down",
  "format": "raw/image",
  "detail": "driver avatar/room avatar/badge/chat",
  "driver": { // avatar 或 badge
    "did": Integer
  },
  "room": { // room avatar
    "rid": Integer
  },
  "from": Integer,  // chat
  "to": Integer
}
```

```
{
  "type": "file",
  "updown": "up",
  "format": "raw/image",
  "length": Integer,
  "detail": "driver avatar/room avatar/chat",
  "driver": { // avatar
    "did": Integer
  },
  "room": { // room avatar
    "rid": Integer
  },
  "from": Integer,  // chat
  "to": Integer
}
```

