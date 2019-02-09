-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
-- -----------------------------------------------------
-- Schema ece1779
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema ece1779
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `ece1779` DEFAULT CHARACTER SET latin1 ;
USE `ece1779` ;

-- -----------------------------------------------------
-- Table `ece1779`.`users`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `ece1779`.`users` ;

CREATE TABLE IF NOT EXISTS `ece1779`.`users` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `username` TEXT NOT NULL,
  `password` TEXT NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = MyISAM
AUTO_INCREMENT = 1
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `ece1779`.`images`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `ece1779`.`images` ;

CREATE TABLE IF NOT EXISTS `ece1779`.`images` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `users_id` INT NOT NULL,
  `filename` TEXT NULL,

  -- INDEX `fk_sections_courses_idx` (`courses_id` ASC),
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


CREATE USER IF NOT EXISTS 'ece1779' IDENTIFIED BY 'secret';
commit;

GRANT ALL ON ece1779.* TO 'ece1779';


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;

