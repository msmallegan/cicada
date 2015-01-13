<?php

// Allow cross-origin resource sharing (CORS)

header('Access-Control-Allow-Origin: *');
date_default_timezone_set('UTC');
try
{

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
frequency_in REAL,
frequency_out REAL
)
DATA;
    $file_db->exec($statement);
    $session = $_POST["session"];
    $location = $_POST["location"];
    $dt_sent = $_POST["dt_sent"];
    $frequency_in = $_POST["frequency_in"];
    if ($frequency_in === "--")
    {
        $frequency_in = null;
    }

    $frequency_out = $_POST["frequency_out"];
    if (!(empty($session)))
    {
        $insert = <<<DATA
INSERT INTO frequencies (
    session, location, dt_sent, frequency_in, frequency_out
) VALUES (:session, :location, :dt_sent, :frequency_in, :frequency_out)
DATA;
        $stmt = $file_db->prepare($insert);
        $stmt->bindParam(':session', $session);
        $stmt->bindParam(':location', $location);
        $stmt->bindParam(':dt_sent', $dt_sent);
        if (is_null($frequency_in))
        {
            $stmt->bindParam(':frequency_in', $frequency_in, PDO::PARAM_NULL);
        }
        else
        {
            $stmt->bindParam(':frequency_in', $frequency_in);
        }

        $stmt->bindParam(':frequency_out', $frequency_out);
        $stmt->execute();

        // Close file db connection

        $file_db = null;
    }
} // End try
catch(PDOException $e)
{

    // Print PDOException message

    echo $e->getMessage();
}

?>
