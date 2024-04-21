const mysql = require('mysql2');
const { unmarshall } = require("@aws-sdk/util-dynamodb");

// MySQL connection configuration
const mysqlConfig = {
    host: process.env.MYSQL_HOST,
    user: process.env.REPORT_AGENT_SQL,
    password: process.env.REPORT_AGENT_PWD,
    database: process.env.REPORT_SCHEMA
};

exports.triggerWriteRobotStateHandler = async (event, context) => {
    console.log(event)
    const connection = mysql.createConnection(mysqlConfig);

    // event = JSON.parse(event.body) // For testing as API
    
    try {
        // Connect to MySQL
        connection.connect();
        console.log("Connected to MySQL");

        // Process each record from the DynamoDB event
        for (let record of event.Records) {
            // Parse record data
            const dynamoData = record.dynamodb.NewImage;
            const processIdVersion = dynamoData.processIdVersion.S;
            const action = getAction(processIdVersion)
            console.log("==ACTION==", action)
            switch (action) {
                case "STATUS":
                    handleUploadRobotStatus(connection, dynamoData);
                    break;
                case "DETAIL":
                    await handleUploadRobotRunDetail(connection, dynamoData);
                    break;
                default:
                    break;
            }
        };
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

/**
 * 
 * @param {string} processIdVersion "pk: PROCESS_ID.PROCESS_VERSION.extra.extra1..."
 * @returns type for action
 */
function getAction(processIdVersion) {
    let elem = processIdVersion.split('.');
    if (elem.length == 2) {
        return "STATUS";
    }
    const extra = elem.slice(2).join(".")
    console.log(extra)
    switch (extra) {
        case "detail":
            return "DETAIL"
        default:
            return extra
    }
}

function handleUploadRobotStatus(connection, dynamoData) {
    const instanceId = dynamoData.instanceId.S;
    const processIdVersion = dynamoData.processIdVersion.S;
    const userId = dynamoData.userId.S;
    const instanceState = dynamoData.instanceState.S;
    const launchTime = dynamoData.launchTime.S;
    const lastRun = dynamoData.lastRun?.S || null;
    const description = dynamoData.description?.S || null;

    // Write to robot_run_log table
    const insertLogQuery = "INSERT INTO robot_run_log (instance_id, process_id_version, user_id, instance_state, launch_time) VALUES (?, ?, ?, ?, ?)";
    const logValues = [instanceId, processIdVersion, userId, instanceState, launchTime];
    connection.query(insertLogQuery, logValues, (error, results, fields) => {
        if (error) throw error;
    });
}

async function handleUploadRobotRunDetail(connection, dynamoData) {
    const processIdVersion = dynamoData.processIdVersion.S;
    const userId = dynamoData.userId.S;
    const [processId, version, _] = processIdVersion.split('.')

    const robotDetail = dynamoData.robotDetail.M
    const stats = unmarshall(robotDetail.stats.M)
    const errors = unmarshall(robotDetail.errors.M)
    const times = unmarshall(robotDetail.time_result.M)
    const kwRun = Object.values(unmarshall(robotDetail.run.L)) // It turn list to object with index is key so we must convert back

    const streamUuid = dynamoData.uuid.S

    const insertOverallQuery = "insert into robot_run_overall (uuid, user_id, process_id, version, failed, passed, error_message, start_time, end_time, elapsed_time) values ?"
    const overallValues = [[
        streamUuid,
        userId,
        processId,
        version,
        stats.failed,
        stats.passed,
        errors.message,
        convertToMySQLDateTime(times.starttime),
        convertToMySQLDateTime(times.endtime),
        convertTimeToMilliseconds(times.elapsed_time)
    ]];

    await connection.promise().query(insertOverallQuery,[overallValues], (error, results, fields) => {
        if (error) throw error;
    });

    const insertKeyWordRunQuery = "insert into report.robot_run_detail (user_id, process_id, version, uuid, kw_id, kw_name, kw_args, kw_status, messages, start_time, end_time) VALUES ?"

    const values = kwRun.map(i => [
        userId.toString(),
        processId.toString(),
        version.toString(),
        streamUuid.toString(),
        i.id.toString(),
        i.kw_name.toString(),
        i.kw_args.toString(),
        i.kw_status.toString(),
        i.messages.toString(),
        parseKeywordDateTime(i.start_time.toString()),
        parseKeywordDateTime(i.end_time.toString())
    ])

    await connection.promise().query(insertKeyWordRunQuery, [values], (error, results, fields) => {
        if (error) throw error;
    });
}

function convertToMySQLDateTime(dateTimeString) {
    return dateTimeString;
}

function parseKeywordDateTime(dateTimeString) {
    // Extract year, month, day, hours, minutes, seconds, and milliseconds from the string
    let year = dateTimeString.slice(0, 4);
    let month = dateTimeString.slice(4, 6);
    let day = dateTimeString.slice(6, 8);
    let hours = dateTimeString.slice(9, 11);
    let minutes = dateTimeString.slice(12, 14);
    let seconds = dateTimeString.slice(15, 17);
    let milliseconds = dateTimeString.slice(18);

    // Create a new Date object with the extracted parts
    let dateObj = new Date(year, month - 1, day, hours, minutes, seconds, milliseconds);

    return dateObj;
}

function convertTimeToMilliseconds(timeString) {
    // Split the time string into hours, minutes, seconds, and milliseconds
    let [hours, minutes, secondsAndMilliseconds] = timeString.split(':');
    
    // Split seconds and milliseconds
    let [seconds, milliseconds] = secondsAndMilliseconds.split('.');
    
    // Convert hours, minutes, seconds, and milliseconds to numbers
    hours = parseInt(hours, 10) || 0;
    minutes = parseInt(minutes, 10) || 0;
    seconds = parseInt(seconds, 10) || 0;
    milliseconds = parseInt(milliseconds, 10) || 0;
    
    // Calculate total milliseconds
    let totalMilliseconds = hours * 3600 + minutes * 60 + seconds;
    
    return totalMilliseconds;
}