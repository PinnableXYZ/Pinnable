-- Adminer 4.8.1 MySQL 8.0.32 dump

SET NAMES utf8mb4;
SET time_zone = '+00:00';
SET foreign_key_checks = 0;
SET sql_mode = 'NO_AUTO_VALUE_ON_ZERO';

SET NAMES utf8mb4;

CREATE TABLE `Account` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `address` varchar(128) NOT NULL,
  `ens` varchar(255) DEFAULT NULL,
  `avatar` varchar(2048) DEFAULT NULL,
  `chain_id` int unsigned NOT NULL DEFAULT '1',
  `dwb_balance` double DEFAULT '0',
  `ens_balance` double DEFAULT '0',
  `websites_order_by` varchar(100) NOT NULL DEFAULT 'name',
  `objects_order_by` varchar(100) NOT NULL DEFAULT 'name',
  `created` int unsigned NOT NULL,
  `last_modified` int unsigned DEFAULT NULL,
  `last_checked` int unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `address` (`address`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Account';


CREATE TABLE `CIDObject` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `object_uuid` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `account_id` int unsigned NOT NULL,
  `filename` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `content_type` varchar(128) NOT NULL,
  `size` bigint unsigned NOT NULL DEFAULT '0',
  `cid` varchar(128) NOT NULL,
  `cid_thumb` varchar(128) DEFAULT NULL,
  `sha256` char(64) NOT NULL,
  `created` int unsigned NOT NULL,
  `last_modified` int unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `object_uuid` (`object_uuid`),
  KEY `account_id` (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='CID Object';


CREATE TABLE `NFTOwnership` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `account_id` int unsigned NOT NULL,
  `chain` varchar(32) NOT NULL,
  `contract` varchar(128) NOT NULL,
  `token_id` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `image_url` varchar(512) DEFAULT NULL,
  `created` int unsigned NOT NULL,
  `last_modified` int unsigned DEFAULT NULL,
  `last_checked` int unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `token` (`chain`,`contract`,`token_id`),
  KEY `account_id` (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='NFT Ownership';


CREATE TABLE `Website` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `account_id` int unsigned NOT NULL,
  `pin_api_uuid` char(36) NOT NULL,
  `name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `title` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `image_url` varchar(512) DEFAULT NULL,
  `subname` varchar(64) DEFAULT NULL,
  `last_known_ipns` varchar(128) DEFAULT NULL,
  `last_known_cid` varchar(128) DEFAULT NULL,
  `size` bigint DEFAULT NULL,
  `created` int unsigned NOT NULL,
  `last_modified` int unsigned DEFAULT NULL,
  `last_checked` int unsigned DEFAULT NULL,
  `last_pinned` int unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `account_name` (`account_id`,`name`),
  UNIQUE KEY `pin_api_uuid` (`pin_api_uuid`),
  UNIQUE KEY `subname` (`subname`),
  KEY `account_id` (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Website';


CREATE TABLE `WebsiteTaskLog` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `website_id` int unsigned NOT NULL,
  `event` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `icon` varchar(128) DEFAULT NULL,
  `ipns` varchar(128) DEFAULT NULL,
  `cid` varchar(128) DEFAULT NULL,
  `size` bigint unsigned DEFAULT NULL,
  `created` int unsigned NOT NULL,
  `last_modified` int unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `website_id` (`website_id`),
  KEY `event` (`event`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Website Task Log';


-- 2025-02-18 06:52:02
