import re

with open('blank.txt', mode ='r')as file:
    lines = file.readlines()
    for line in lines:
        m = re.search('(?<=")(.*)(?=")', line.split("?")[-1])[0]
        n = re.search('(?<=\>)(.*)(?=\<)', line.split("?")[-1])[0]
        print('{' + ' \"label\" : "{}", \"value\" : {} '.format(n, m) + '},')