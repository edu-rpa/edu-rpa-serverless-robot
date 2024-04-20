import argparse
import os
from robot.api import ExecutionResult, ResultVisitor
from robot.model import TestCase
import boto3

class MyResultVisitor(ResultVisitor):
    def __init__(self):
        self.kw_run = []
        self.ids = {
            0 : {
                "id" : "",
                "cur_child_count" : 0
            }
        }

    def generate_id(self, object, parent):
        # Generate a unique ID using the id_counter and the id_stack
        id = ""
        hashKey = hash(object)
        if(parent and not isinstance(parent, TestCase)):
            if(parent.type == 'ITERATION'):
                parentHashKey = hash(parent.parent)
            else:
                parentHashKey = hash(parent)
        else:
            parentHashKey = 0  
        parentObject = self.ids[parentHashKey]
        curChildCount = parentObject["cur_child_count"]
        curChildCount += 1
        parentObject["cur_child_count"] = curChildCount
        parentId = parentObject['id']
        id = f"{parentId+'.' if parentId else ''}{curChildCount}"
        
        self.ids[hashKey] = {
            "id" : id,
            "cur_child_count": 0,
        }
        
        return id

    def visit_for(self, for_):
        # Push the current 'for' loop's ID to the id_stack
        kw_id = self.generate_id(for_, for_.parent)
        self.kw_run.append({
            "id": kw_id,
            "kw_name": for_.type,
            "kw_args": for_.name,
            "kw_status": for_.status,
            "start_time": for_.starttime,
            "end_time": for_.endtime,
        })
        for_.body.visit(self)
    def visit_if_branch(self, branch):
        kw_id = self.generate_id(branch, branch.parent.parent)
        self.kw_run.append({
            "id": kw_id,
            "kw_name": branch.type,
            "kw_args": branch.name,
            "kw_status": branch.status,
            "start_time": branch.starttime,
            "end_time": branch.endtime,
        })
        branch.body.visit(self)
    
    def visit_keyword(self, kw):
        # Generate the ID based on the current 'for' loop hierarchy
        kw_id = self.generate_id(kw, kw.parent)
        kw_args = getattr(kw, 'args', None)  # Check if 'args' attribute exists
        self.kw_run.append({
            "id": kw_id,
            "kw_name": kw.name,
            "kw_args": kw_args,
            "kw_status": kw.status,
            "start_time": kw.starttime,
            "end_time": kw.endtime,
            "messages": str(kw.messages[0] if len(kw.messages) else "")
        })


def parse(output_xml_path, user_id, process_id_version, table_name="robot"): 
    result = ExecutionResult(output_xml_path)
    stats = result.statistics
    stat_result = {
        'failed': stats.total.failed,
        'passed': stats.total.passed
    }

    errors = result.errors
    visitor = MyResultVisitor()
    errors_result = {
        "error": True if errors else False,
        "message": str(errors)
    }

    result.visit(visitor)

    # Get the serialize object
    kw_run = visitor.kw_run

    dynamodb = boto3.resource('dynamodb')
    table_name = 'robot'
    table = dynamodb.Table(table_name)

    table.put_item(Item = {
        "userId" : user_id,
        "processIdVersion": process_id_version,
        "uuid": os.environ["UUID_STREAM"],
        "robotDetail": {
            "stats": stat_result,
            "errors": errors_result,
            "run": kw_run
        }
    })
    
def parse_args():
    parser = argparse.ArgumentParser(description="Parse and add robot detail")
    
    # Define your command-line arguments
    parser.add_argument('--output_xml_path', type=str, help='path of output.xml')
    parser.add_argument('--user_id', type=str, help='user id')
    parser.add_argument('--process_id_version', type=str, help='process id with version seperate by .')
    # Add more arguments as needed
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    parse(**vars(args))