from employee_dao import Impiegato, EmployeeDao
import json


dao = EmployeeDao()

print(json.dumps([imp.__dict__ for imp in dao.findImpiegati()]))

