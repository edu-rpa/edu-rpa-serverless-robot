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
            const processIdVersion = dynamoData.process_id_version.S;
            const action = getAction(processIdVersion)
            switch (action) {
                case "STATUS":
                    handleUploadRobotStatus(connection, dynamoData);
                    break;
                case "DETAIL":
                    handleUploadRobotRunDetail(connection, dynamoData);
                    break;
                default:
                    break;
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
    switch (extra) {
        case "detail":
            return "DETAIL"
        default:
            return extra
    }
}

function handleUploadRobotStatus(connection, dynamoData) {
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
}

function handleUploadRobotRunDetail(connection, dynamoData) {
    const instanceId = dynamoData.instance_id.S;
    const processIdVersion = dynamoData.process_id_version.S;
    const userId = dynamoData.user_id.S;
    const [processId, version, _] = processIdVersion.split('.')

    stats = AWS.DynamoDB.Converter.marshall(dynamoData.stats.M)
    errors = AWS.DynamoDB.Converter.marshall(dynamoData.errors.M)
    kwRun = AWS.DynamoDB.Converter.marshall(dynamoData.run.L)
    streamUuid = dynamoData.uuid.S

    const insertOverallQuery = "insert into robot_run_overall (instance_id, user_id, process_id, version, failed, passed, error_message) values (?,?,?,?,?,?,?)"
    const overallValues = [instanceId, userId , processId, version, stats.failed, stats.passed, errors.message];

    connection.query(insertOverallQuery, overallValues, (error, results, fields) => {
        if (error) throw error;
    });

    const insertKeyWordRunQuery = "insert into report.robot_run_detail (user_id, process_id, version, uuid, kw_id, kw_name, kw_args, kw_status, messages, start_time, end_time) VALUES (?,?,?,?,?,?,?,?,?,?,?)"
    const values = kwRun.map(i => [userId, processId, version, streamUuid, i.kw_id, i.kw_name, i.kw_args, i.kw_status, i.messages, i.start_time, i.end_time])
    connection.query(insertKeyWordRunQuery, values, (error, results, fields) => {
        if (error) throw error;
    });
}
