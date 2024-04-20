const mysql = require('mysql2');
const { unmarshall } = require("@aws-sdk/util-dynamodb");

// MySQL connection configuration
const mysqlConfig = {
    host: "edu-rpa-db-dev.cahnyqo389dg.ap-southeast-2.rds.amazonaws.com",
    user: "report_agent",
    password: "rA93{1L8=9D!",
    database: "report"
};
const connection = mysql.createConnection(mysqlConfig);

connection.connect();

const insertKeyWordRunQuery = "insert into report.robot_run_detail (user_id, process_id, version, uuid, kw_id, kw_name, kw_args, kw_status, messages, start_time, end_time) VALUES ?"
const values =   [
    [
      '7',
      'Process_94XTLQD',
      '1',
      'hsddkfhoi1323182308919237-123jsdgdfjhsjdfhb',
      '1',
      'EduRPA.Google.Classroom.Set Up Classroom Connection',
      './devdata/token-classroom.json',
      'PASS',
      '',
      '20240420 13:48:02.979',
      '20240420 13:48:02.979'
    ],
    [
      '7',
      'Process_94XTLQD',
      '1',
      'hsddkfhoi1323182308919237-123jsdgdfjhsjdfhb',
      '2',
      'EduRPA.Google.Classroom.Create Course',
      '${COURSE_NAME},${USER}',
      'FAIL',
      'file_cache is only supported with oauth2client<4.0.0',
      '20240420 13:48:02.979',
      '20240420 13:48:07.637'
    ],
    [
      '7',
      'Process_94XTLQD',
      '1',
      'hsddkfhoi1323182308919237-123jsdgdfjhsjdfhb',
      '3',
      'BuiltIn.Log',
      'Course ID: ${course_id}',
      'NOT RUN',
      '',
      '20240420 13:48:07.638',
      '20240420 13:48:07.638'
    ]
  ]
connection.promise().query(insertKeyWordRunQuery, [values], (error, results, fields) => {
    if (error) throw error;
});
connection.end();