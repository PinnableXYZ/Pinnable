-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: db
-- Generation Time: Oct 23, 2023 at 09:37 AM
-- Server version: 8.0.32
-- PHP Version: 8.1.15

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

--
-- Database: `ivalice`
--

-- --------------------------------------------------------

--
-- Table structure for table `Account`
--

CREATE TABLE `Account` (
  `id` int UNSIGNED NOT NULL,
  `address` varchar(128) NOT NULL,
  `ens` varchar(255) DEFAULT NULL,
  `avatar` varchar(2048) DEFAULT NULL,
  `chain_id` int UNSIGNED NOT NULL DEFAULT '1',
  `dwb_balance` double DEFAULT '0',
  `created` int UNSIGNED NOT NULL,
  `last_modified` int UNSIGNED DEFAULT NULL,
  `last_checked` int UNSIGNED DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Account';

-- --------------------------------------------------------

--
-- Table structure for table `NFTOwnership`
--

CREATE TABLE `NFTOwnership` (
  `id` int UNSIGNED NOT NULL,
  `account_id` int UNSIGNED NOT NULL,
  `chain` varchar(32) NOT NULL,
  `contract` varchar(128) NOT NULL,
  `token_id` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `image_url` varchar(512) DEFAULT NULL,
  `created` int UNSIGNED NOT NULL,
  `last_modified` int UNSIGNED DEFAULT NULL,
  `last_checked` int UNSIGNED DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='NFT Ownership';

-- --------------------------------------------------------

--
-- Table structure for table `Website`
--

CREATE TABLE `Website` (
  `id` int UNSIGNED NOT NULL,
  `account_id` int UNSIGNED NOT NULL,
  `pin_api_uuid` char(36) NOT NULL,
  `name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `last_known_ipns` varchar(128) DEFAULT NULL,
  `last_known_cid` varchar(128) DEFAULT NULL,
  `size` bigint DEFAULT NULL,
  `created` int UNSIGNED NOT NULL,
  `last_modified` int UNSIGNED DEFAULT NULL,
  `last_checked` int UNSIGNED DEFAULT NULL,
  `last_pinned` int UNSIGNED DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Website';

-- --------------------------------------------------------

--
-- Table structure for table `WebsiteTaskLog`
--

CREATE TABLE `WebsiteTaskLog` (
  `id` int UNSIGNED NOT NULL,
  `website_id` int UNSIGNED NOT NULL,
  `event` varchar(4000) NOT NULL,
  `icon` varchar(128) DEFAULT NULL,
  `ipns` varchar(128) DEFAULT NULL,
  `cid` varchar(128) DEFAULT NULL,
  `size` bigint UNSIGNED DEFAULT NULL,
  `created` int UNSIGNED NOT NULL,
  `last_modified` int UNSIGNED DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Website Task Log';

--
-- Indexes for dumped tables
--

--
-- Indexes for table `Account`
--
ALTER TABLE `Account`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `address` (`address`);

--
-- Indexes for table `NFTOwnership`
--
ALTER TABLE `NFTOwnership`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `token` (`chain`,`contract`,`token_id`),
  ADD KEY `account_id` (`account_id`);

--
-- Indexes for table `Website`
--
ALTER TABLE `Website`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `account_name` (`account_id`,`name`),
  ADD UNIQUE KEY `pin_api_uuid` (`pin_api_uuid`),
  ADD KEY `account_id` (`account_id`);

--
-- Indexes for table `WebsiteTaskLog`
--
ALTER TABLE `WebsiteTaskLog`
  ADD PRIMARY KEY (`id`),
  ADD KEY `website_id` (`website_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `Account`
--
ALTER TABLE `Account`
  MODIFY `id` int UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `NFTOwnership`
--
ALTER TABLE `NFTOwnership`
  MODIFY `id` int UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `Website`
--
ALTER TABLE `Website`
  MODIFY `id` int UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `WebsiteTaskLog`
--
ALTER TABLE `WebsiteTaskLog`
  MODIFY `id` int UNSIGNED NOT NULL AUTO_INCREMENT;
COMMIT;
