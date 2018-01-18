DROP TABLE IF EXISTS nodes_address,nodes_tags,ways_nodes,ways_tags,ways,nodes;


CREATE TABLE nodes (
    `id` BIGINT PRIMARY KEY NOT NULL ,
    `lat` REAL,
    `lon` REAL,
    `user` TEXT,
    `uid` INTEGER,
    `version` INTEGER,
    `changeset` INTEGER,
    `timestamp` TEXT
) CHARACTER SET 'utf8' COLLATE 'utf8_unicode_ci';

CREATE TABLE nodes_address (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT NOT NULL ,
    `node_id` BIGINT NOT NULL,
    `number` TEXT,
    `unit` TEXT,
    `street` TEXT,
    `city` TEXT,
    `state` TEXT,
    `country` TEXT,
    `postcode` TEXT,
    CONSTRAINT  FOREIGN KEY (`node_id`) REFERENCES nodes(`id`)
) CHARACTER SET 'utf8' COLLATE 'utf8_unicode_ci';


CREATE TABLE nodes_tags (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT NOT NULL,
    `node_id` BIGINT NOT NULL,
    `key` TEXT,
    `value` TEXT,
    CONSTRAINT  FOREIGN KEY (`node_id`) REFERENCES nodes(`id`)
) CHARACTER SET 'utf8' COLLATE 'utf8_unicode_ci';



CREATE TABLE ways (
    `id` BIGINT PRIMARY KEY NOT NULL,
    `user` TEXT,
    `uid` INTEGER,
    `version` TEXT,
    `changeset` INTEGER,
    `timestamp` TEXT
) CHARACTER SET 'utf8' COLLATE 'utf8_unicode_ci';

CREATE TABLE ways_tags (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT NOT NULL,
    `ways_id` BIGINT NOT NULL,
    `key` TEXT NOT NULL,
    `value` TEXT NOT NULL,
    `type` TEXT,
    CONSTRAINT FOREIGN KEY (`ways_id`) REFERENCES ways(id)
) CHARACTER SET 'utf8' COLLATE 'utf8_unicode_ci';

    

CREATE TABLE ways_nodes (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT NOT NULL,
    `ways_id` BIGINT NOT NULL,
    `node_id` BIGINT NOT NULL,
    `position` BIGINT NOT NULL,
    CONSTRAINT FOREIGN KEY (`ways_id`) REFERENCES ways(id),
    CONSTRAINT FOREIGN KEY (`node_id`) REFERENCES nodes(id)
) CHARACTER SET 'utf8' COLLATE 'utf8_unicode_ci';

