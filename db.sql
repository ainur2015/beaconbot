-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Хост: ficsik.ru
-- Время создания: Окт 10 2024 г., 19:31
-- Версия сервера: 8.0.39-AlmaLinux 9.2
-- Версия PHP: 8.3.0


SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;



--
-- Структура таблицы `admin_logs`
--

CREATE TABLE `admin_logs` (
  `id` int NOT NULL,
  `vk_id` bigint NOT NULL,
  `message` text NOT NULL,
  `times` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Структура таблицы `aliases`
--

CREATE TABLE `aliases` (
  `id` int NOT NULL,
  `code` text NOT NULL,
  `text` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Структура таблицы `ip_port`
--

CREATE TABLE `ip_port` (
  `id` int NOT NULL,
  `ip_address` text NOT NULL,
  `port` text NOT NULL,
  `times` text NOT NULL,
  `vk_id` text NOT NULL,
  `ok` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Структура таблицы `lister`
--

CREATE TABLE `lister` (
  `id` int NOT NULL,
  `server` text NOT NULL,
  `times` text NOT NULL,
  `online` text NOT NULL,
  `port` varchar(256) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Структура таблицы `onlines`
--

CREATE TABLE `onlines` (
  `id` int NOT NULL,
  `daysmax` text,
  `dayssred` text,
  `daysmin` text,
  `nedelmax` text,
  `nedelsred` text,
  `nedelmin` text,
  `mecmax` text,
  `mecred` text,
  `mecmin` text,
  `vse` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Структура таблицы `pinglist`
--

CREATE TABLE `pinglist` (
  `id` int NOT NULL,
  `ip_address` text NOT NULL,
  `port` text NOT NULL,
  `protocol` text NOT NULL,
  `times` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Структура таблицы `psettings`
--

CREATE TABLE `psettings` (
  `id` int NOT NULL,
  `bot` int NOT NULL DEFAULT '1',
  `times` text NOT NULL,
  `timesport` int NOT NULL,
  `uptime` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Структура таблицы `server`
--

CREATE TABLE `server` (
  `id` int NOT NULL,
  `alias` text,
  `created_at` text NOT NULL,
  `from_id` text NOT NULL,
  `image_url` varchar(255) NOT NULL DEFAULT 'start.jpg',
  `ip_address` text NOT NULL,
  `ips` text NOT NULL,
  `line_color` varchar(255) NOT NULL DEFAULT 'red',
  `cheating` int NOT NULL DEFAULT '0',
  `port` int NOT NULL,
  `ok` int NOT NULL DEFAULT '1',
  `online` text NOT NULL,
  `last_proxy` text NOT NULL,
  `onlines` text,
  `active` int NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `stats`
--

CREATE TABLE `stats` (
  `id` int NOT NULL,
  `owner_id` text NOT NULL,
  `vk_id` text NOT NULL,
  `times` text NOT NULL,
  `name` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Структура таблицы `users`
--

CREATE TABLE `users` (
  `id` int NOT NULL,
  `vk_id` int NOT NULL,
  `vip` int NOT NULL DEFAULT '0',
  `admin` int NOT NULL DEFAULT '0',
  `ban` int NOT NULL DEFAULT '0',
  `lang` varchar(15) NOT NULL DEFAULT 'ru',
  `times` varchar(255) NOT NULL DEFAULT 'NULL',
  `viptimes` text,
  `vipfull` int NOT NULL DEFAULT '0',
  `checkport` int NOT NULL,
  `daysclick` text NOT NULL,
  `click` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- --------------------------------------------------------

--
-- Структура таблицы `zapret`
--

CREATE TABLE `zapret` (
  `id` int NOT NULL,
  `slovo` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

--
-- Индексы сохранённых таблиц
--

--
-- Индексы таблицы `admin_logs`
--
ALTER TABLE `admin_logs`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `aliases`
--
ALTER TABLE `aliases`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `ip_port`
--
ALTER TABLE `ip_port`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `lister`
--
ALTER TABLE `lister`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `onlines`
--
ALTER TABLE `onlines`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `pinglist`
--
ALTER TABLE `pinglist`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `psettings`
--
ALTER TABLE `psettings`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `server`
--
ALTER TABLE `server`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `stats`
--
ALTER TABLE `stats`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `zapret`
--
ALTER TABLE `zapret`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT для сохранённых таблиц
--

--
-- AUTO_INCREMENT для таблицы `admin_logs`
--
ALTER TABLE `admin_logs`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `aliases`
--
ALTER TABLE `aliases`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `ip_port`
--
ALTER TABLE `ip_port`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `lister`
--
ALTER TABLE `lister`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `onlines`
--
ALTER TABLE `onlines`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `pinglist`
--
ALTER TABLE `pinglist`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `psettings`
--
ALTER TABLE `psettings`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `server`
--
ALTER TABLE `server`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `stats`
--
ALTER TABLE `stats`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `users`
--
ALTER TABLE `users`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `zapret`
--
ALTER TABLE `zapret`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
