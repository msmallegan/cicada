<?php

date_default_timezone_set('UTC');

try {

// Create (connect to) SQLite database in file
$file_db = new PDO('sqlite:frequencies.sqlite3');

// Set errormode to exceptions
$file_db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

$statement = <<<DATA
CREATE TABLE IF NOT EXISTS frequencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session TEXT,
    location TEXT,
    dt_sent DATETIME,
    dt_received DATETIME DEFAULT CURRENT_TIMESTAMP,
    frequency REAL
)
DATA;
$file_db->exec($statement);

$session = $_POST["session"];
$location = $_POST["location"];
$dt_sent = $_POST["dt_sent"];
$frequency = $_POST["frequency"];

$insert = <<<DATA
INSERT INTO frequencies (session, location, dt_sent, frequency)
VALUES (:session, :location, :dt_sent, :frequency)
DATA;
$stmt = $file_db->prepare($insert);

$stmt->bindParam(':session', $session);
$stmt->bindParam(':location', $location);
$stmt->bindParam(':dt_sent', $dt_sent);
$stmt->bindParam(':frequency', $frequency);

$stmt->execute();

// Close file db connection
$file_db = null;

}
catch(PDOException $e) {
    // Print PDOException message
    echo $e->getMessage();
}

?>
