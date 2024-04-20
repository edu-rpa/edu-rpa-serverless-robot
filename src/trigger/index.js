const mysql = require('mysql2');

// MySQL connection configuration
const mysqlConfig = {
    host: process.env.MYSQL_HOST,
    user: process.env.REPORT_AGENT_SQL,
    password: process.env.REPORT_AGENT_PWD,
    database: process.env.REPORT_SCHEMA
};

exports.triggerWriteRobotStateHandler = async (event, context) => {
    console.log(mysqlConfig);
    const connection = mysql.createConnection(mysqlConfig);

    try {
        // Connect to MySQL
        connection.connect();
        console.log("Connected to MySQL");

        // Process each record from the DynamoDB event
        event.Records.forEach((record) => {
            // Parse record data
            const dynamoData = record.dynamodb.NewImage;
            const instanceId = dynamoData.instance_id.S;
            const processIdVersion = dynamoData.process_id_version.S;
            const userId = dynamoData.user_id.S;
            const instanceState = dynamoData.instance_state.S;
            const launchTime = dynamoData.launch_time.S;
            const lastRun = dynamoData.last_run?.S || null;
            const description = dynamoData.description?.S || null;

            // Write to robot_run_log table
            const insertLogQuery = "INSERT INTO robot_run_log (instance_id, process_id_version, user_id, instance_state, launch_time) VALUES (?, ?, ?, ?, ?)";
            const logValues = [instanceId, processIdVersion, userId, instanceState, launchTime];
            connection.query(insertLogQuery, logValues, (error, results, fields) => {
                if (error) throw error;
            });

            // Write to robot_run_result table if last_run field is present
            if (lastRun !== null) {
                const insertResultQuery = "INSERT INTO robot_run_result (instance_id, process_id_version, user_id, last_run, description) VALUES (?, ?, ?, ?, ?)";
                const resultValues = [instanceId, processIdVersion, userId, lastRun, description];
                connection.query(insertResultQuery, resultValues, (error, results, fields) => {
                    if (error) throw error;
                });
            }
        });

    } catch (error) {
        console.error("Error while connecting to MySQL:", error);
        throw error;

    } finally {
        // Close MySQL connection
        if (connection && connection.state !== 'disconnected') {
            connection.end();
            console.log("MySQL connection is closed");
        }
    }

    return {
        statusCode: 200,
        body: JSON.stringify('Data processed successfully')
    };
};


exports.triggerWriteRobotRunResultHandler = async (event, context) => {
    console.log(mysqlConfig);
    const connection = mysql.createConnection(mysqlConfig);

    try {
        // Connect to MySQL
        connection.connect();
        console.log("Connected to MySQL");

        // Process each record from the DynamoDB event
        event.Records.forEach((record) => {
            // Parse record data
            const dynamoData = record.dynamodb.NewImage;
        });

    } catch (error) {
        console.error("Error while connecting to MySQL:", error);
        throw error;

    } finally {
        // Close MySQL connection
        if (connection && connection.state !== 'disconnected') {
            connection.end();
            console.log("MySQL connection is closed");
        }
    }

    return {
        statusCode: 200,
        body: JSON.stringify('Data processed successfully')
    };
};
