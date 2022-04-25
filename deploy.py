import requests
import csv
from distutils.log import error
import json
from typing import List
import sys
import urllib3

#Program to handle the deployment of excersises to the students


sys.tracebacklimit = 0#Dont post traceback


#Access token
access_token = ""

#Id of the parent group
group_id = -1
#Assignment ID
project_id = -1
#url of gitlab api
url="https://git.app.uib.no/api/v4"

#csv file of students in format "firstname.lastname@student.uib.no", subgrupname will then be firstname.lastname
students="students.csv"

#Cookie
s = requests.Session()
s.headers.update({'Content-type': 'application/json', 'PRIVATE-TOKEN': access_token})

def get_all_users(file:str)->List[str]:
    ls = []
    with open(file, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            ls.append(row[0])
    return ls

#Gets  
def get_group(group:int)->json:
    r = requests.get(url+"/groups/"+str(group),headers=headers)
    r.raise_for_status()
    return r.json()

def get_project(project_id:int)->json:
    r = requests.get(url+"/projects/"+str(project_id),headers=headers)
    r.raise_for_status()
    return r.json()

def get_group1(name)->json:
    r = s.get(url+"/groups/"+str(group_id)+"/subgroups")
    r.raise_for_status()
    for sub_group in r.json():
        if sub_group["name"]==name:
            return sub_group
    raise Exception("No subgroup with name:"+name)

def kill_subgroups(group_id:int):
    r = s.get(url+"/groups/"+str(group_id)+"/subgroups")
    print(r.json())
    r.raise_for_status()
    for sub_group in r.json():
        r=s.delete(url+"/groups/"+str(sub_group["id"]))

def student_page_exists(student_id:str)->bool:
    try:
        get_group1(student_id)
        return True
    except:
        return False

def create_student_page(project_id:int,student:str, group:int):
    student_email= student
    student_id = student.split("@")[0]

    if not student_page_exists(student_id):
        print(f'Creating page for %{student_id}')
        gitlab_url = url+"/groups/?parent_id="+str(group)
        urllib3.disable_warnings()
        data = {'name': student_id, 'path': student_id.replace(".","")}
        r = s.post(gitlab_url, verify=True, json=data)
    else:
        print(f'{student_id} allready exists.')
    
    try:
        student_group = get_group1(student_id)
    except:
        print(f'No group with name {student_id}')
        return
    #add project to subgroup
    data = {'namespace_path':student_group["full_path"]}
    print(f'Forking project to {student_group["full_path"]}')
    r = s.post(url+"/projects/"+str(project_id)+"/fork", json=data)#create fork
    #print(r.json())
    try:
        r.raise_for_status()
    except:
        error(f'Could not fork project to {student_group["full_path"]}: {r.json()}')
        return
    #Add student to subgroup
    print(f'Sending invite to {student_email}')
    r = s.post(url+"/groups/"+str(student_group["id"])+"/invitations", json={'email':student_email, 'access_level':40})
    try:
        r.raise_for_status()
    except:
        print(f'Unable to send invite to {student_email}')

def __main__(): 
    if("-d" in sys.argv):
        sys.tracebacklimit = 3
    if("-del" in sys.argv):
        kill_subgroups(group_id)
    for student in get_all_users(students):
        create_student_page(project_id, student, group_id)


if __name__ == '__main__':
    __main__()
