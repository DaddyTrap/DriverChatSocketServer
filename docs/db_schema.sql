create table Driver(
  did INT NOT NULL AUTO_INCREMENT,
  username VARCHAR(32) NOT NULL,
  password CHAR(64) NOT NULL,
  name VARCHAR(40) NOT NULL,
  avatar VARCHAR(64),
  badge VARCHAR(32),
  created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  primary key(did)
);

create table Room(
  rid INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(40) NOT NULL,
  direction VARCHAR(40),
  activeness INT,
  created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  primary key(rid)
); 

create table UserStar(
  star_id INT NOT NULL AUTO_INCREMENT,
  did INT NOT NULL,
  rid INT NOT NULL,
  primary key(star_id),
  foreign key(did) references Driver(did) on delete cascade on update cascade,
  foreign key(rid) references Room(rid) on delete cascade on update cascade
);

create table BannedDriver(
  ban_id INT NOT NULL AUTO_INCREMENT,
  did INT NOT NULL,
  rid INT NOT NULL,
  primary key(ban_id),
  foreign key(did) references Driver(did) on delete cascade on update cascade,
  foreign key(rid) references Room(rid) on delete cascade on update cascade
);
