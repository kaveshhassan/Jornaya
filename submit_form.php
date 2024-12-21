<?php
// File path for the queue and passwords
$queue_file = "queue.json";
$passwords_file = "passwords.txt";

// Check if form data is submitted via POST
if ($_SERVER["REQUEST_METHOD"] === "POST") {
    // Extract form data
    $form_data = [
        "FirstName" => $_POST["FirstName"],
        "LastName" => $_POST["LastName"],
        "Email" => $_POST["Email"],
        "PhoneNumber" => $_POST["PhoneNumber"],
        "State" => $_POST["State"],
        "City" => $_POST["City"],
        "ZipCode" => $_POST["ZipCode"],
        "Address" => $_POST["Address"]
    ];

    // Match proxy credentials based on City or State
    $passwords = file($passwords_file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    $proxy_pass = null;

    foreach ($passwords as $line) {
        list($key, $password) = explode(" : ", $line, 2);
        if (strcasecmp(trim($key), $form_data["City"]) === 0 || strcasecmp(trim($key), $form_data["State"]) === 0) {
            $proxy_pass = trim($password);
            break;
        }
    }

    if (!$proxy_pass) {
        echo "No matching proxy password found for City: {$form_data['City']} or State: {$form_data['State']}.";
        exit;
    }

    // Static proxy username
    $proxy_user = 'Kavesh';

    // Prepare form data including proxy credentials
    $form_data["proxy_user"] = $proxy_user;
    $form_data["proxy_pass"] = $proxy_pass;

    // Check if the queue file exists
    if (file_exists($queue_file)) {
        $queue = json_decode(file_get_contents($queue_file), true);
    } else {
        $queue = [];
    }

    // Add the new form data to the queue
    $queue[] = $form_data;

    // Save the updated queue back to the file
    file_put_contents($queue_file, json_encode($queue, JSON_PRETTY_PRINT));

    echo "Form submitted successfully.<br>";

    // Execute the Python script
    $command = escapeshellcmd("python process_form.py");
    $output = [];
    $result_code = 0;

    exec($command, $output, $result_code);

    if ($result_code === 0) {
        echo "Python script executed successfully.<br>";
        echo "Output:<br>" . implode("<br>", $output);
    } else {
        echo "Error executing Python script. Return code: $result_code<br>";
        echo "Output:<br>" . implode("<br>", $output);
    }
} else {
    echo "Invalid request method.";
}
?>
