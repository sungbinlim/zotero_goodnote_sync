#--------------------------------#
# Zotero 에 저장된 pdf 파일들을 Dropbox 의 특정 폴더 위치로 생성날짜별로 정리하는 프로그램
# This program sorts pdf files in Zotero folder due to the added date
#--------------------------------#

import sys, os
from shutil import move, copyfile
import time

zotero_route = os.path.expanduser("~/Dropbox/[DailyArticle]/[Zotero]/storage/")
target_route = os.path.expanduser("~/Dropbox/[DailyArticle]/[ReadingList]/")
goodnote_route = os.path.expanduser("~/Dropbox/[GoodNotes]/[Articles]/[ReadingList]/")

# Main programs
def FileManager(goodnote=False):
    input_date = eval(input("Which date do you want to sort out? : "))
    goodnote = input("Move annoteted files in goodnote? (press yes): ")
    Zotero = ParseZotero(input_date=input_date, zotero_route=zotero_route, target_route=target_route)
    Zotero.directory_generator()
    Zotero.file_copy()
    if goodnote in ["yes", "y"]:
        Goodnotes = ParseGoodnotes(input_date=Zotero.input_date)
        annotate_list = Goodnotes.pdfs_in_goodnote()
        annotate_root = Goodnotes.listup_roots()
        move_folders_zotero(annotate_list, annotate_root)
        move_folders_target(annotate_list, target_route)
    myprint("Syncronization is completed")    
    
class ParseGoodnotes(object):
    def __init__(self, input_date="today",
                       goodnote_route=goodnote_route, 
                       zotero_route=zotero_route, 
                       target_route=target_route,
                ):
        self.pdf_list = []
        self.input_date = input_date
        if check_routes(goodnote_route, zotero_route, target_route):
            self.goodnote_route, self.zotero_route, self.target_route = goodnote_route, zotero_route, target_route
        else:
            raise ValueError("Given routes are not proper.")
        self.zotero = ParseZotero(input_date=self.input_date,
                                  zotero_route=self.zotero_route,
                                  target_route=self.target_route)            
    
    def listup_roots(self):
        gathered_dict = self.zotero.file_gathers(goodnote=True)[1]
        listup = {}
        files_lists = [files for files in gathered_dict.values()]
        for files in files_lists:
            for file in files:
                route = file.split("/")
                filename = route.pop()
                route = "/".join(route)
                listup[filename] = route
        
        return listup

    def pdfs_in_goodnote(self):
        pdf_digger(self.goodnote_route, self.pdf_list)
        
        return self.pdf_list

def pdf_digger(route, list_):
    route_pdf = os.path.abspath(route)
    if pdf_checker(route_pdf):
        list_.append(route_pdf)
    elif os.path.isdir(route):
        sub_routes = [route + sub_route + "/" for sub_route in os.listdir(route)]
        for sub_route in sub_routes:
            pdf_digger(sub_route, list_)
    else:
        pass

class ParseZotero(object):
    def __init__(self, input_date="today", zotero_route=zotero_route, target_route=target_route):
        if check_routes(zotero_route, target_route):
            self.zotero_route, self.target_route = zotero_route, target_route
        else:
            raise ValueError("Given routes are not proper.")
        
        if (input_date == "today") or (type(input_date) == tuple) or (int(input_date) in range(1,13)):
            self.input_date = transform_date(input_date)
        else:
            raise NotImplementedError("Input date shoule be tuple or month information")

        self.file_routes = {}
        self.oldfile_routes = {}
        self.error_route = []
    
    #ToDo: refactoring
    def file_gathers(self, goodnote=False):
        dirs = os.listdir(self.zotero_route)
        for dirname in dirs:
            dir_route = self.zotero_route + dirname + "/"
            try: # works only for directories
                for filename in os.listdir(dir_route):
                    file_route = dir_route + filename
                    if pdf_checker(file_route):
                        gathered_date = date_gather(file_route) # gather created date
                        if type(gathered_date) == tuple: # date is gathered well
                            if gathered_date < self.input_date: 
                                if goodnote:
                                    self.gathering(gathered_date, self.oldfile_routes, file_route) # for goodnotes
                                else: 
                                    continue
                            else: 
                                self.gathering(gathered_date, self.file_routes, file_route) # for zotero
                        else:
                            self.error_route.append(gathered_date) # collect error routes
                    else:
                        continue
            except NotADirectoryError:
                continue

        if len(self.error_route):
            return self.file_routes, self.oldfile_routes, self.error_route
        else:
            return self.file_routes, self.oldfile_routes, None
    
    def gathering(self, date, file_routes, file_route):
        if append_rule(date, file_routes, file_route) == "new":
            file_routes[date].append(file_route)
        elif append_rule(date, file_routes, file_route) == "exists":
            pass
        elif append_rule(date, file_routes, file_route) == "new_key":
            file_routes[date] = [file_route]

    def directory_names(self):
        folder_date = [date for date in self.file_gathers()[0].keys()]
        folder_name = [self.target_route + date_converter(date) + "/" for date in folder_date]

        try:
            return zip(folder_name, folder_date)
        except ValueError:
            return None

    def directory_generator(self):
        for directory_name, _ in self.directory_names():
            try:
                os.mkdir(directory_name)
            except FileExistsError:
                continue
    
    def file_copy(self):
        for directory_name, key in self.directory_names():
            files = self.file_gathers()[0][key]
            pdfs = [file.split("/")[-1] for file in files]
            dsts = [directory_name + pdf for pdf in pdfs]
            for file, dst in zip(files, dsts):
                try:
                    copyfile(file, dst)
                except FileExistsError:
                    continue

# ===== Auxiliary Codes ====== #
# Check a given file is PDF
def pdf_checker(file_route):
    try:
        check_file = os.path.isfile(file_route)
        ispdf = (file_route.split(".")[-1] == "pdf")
        if (check_file) & (ispdf):
            return True
        else:
            return False
    except:
        return False

# Gather created date for given file
def date_gather(file_route):
    try:
        ctime = os.path.getctime(file_route)
        return time.gmtime(ctime)[:3] # return (yyyy, mm, dd)
    except FileNotFoundError:
        return file_route

# check_routes(zotero_route, target_route) = True
def check_routes(*args):
    check_values = [os.path.isdir(route) for route in args]
    return min(check_values)

def transform_date(date):
    today_date = time.localtime()[0:2] # (yyyy, mm)
    try:
        if date=="today": 
            return time.localtime()[0:3]
        elif type(date) == tuple:
            try:
                if len(date) > 2:
                    return (yy2yyyy(date[0]), date[1], date[2])
                else:
                    return (yy2yyyy(date[0]), date[1], 1)
            except:
                raise NotImplementedError("input date is not valid!")
        elif int(date) in range(1, 13): # if input date is month
            return (time.localtime()[0],int(date), 1)
        
    except ValueError:
        Warning("Given date is not valid. We use {} instead.".format(today_date))
        return transform_date(date=time.localtime()[0:2])

def yy2yyyy(year):
    if year > 1900:
        return year
    else:
        year += 2000
        return year

def yyyy2yy(year):
    if year > time.localtime()[0]:
        raise ValueError("{} is not valid year".format(year))
    else:
        return (year - 2000)

def m2mm(month):
    if month > 12:
        raise ValueError("Month cannot be greater than 12!")
    elif month < 10:
        return "0" + str(month)
    else:
        return str(month)

def day2week(day):
    if day > 31:
        raise ValueError("Day cannot be greater than 31!")
    else:
        week = (min(27, day) // 7) + 1
        return week

#ToDo: update converters
def date_converter(date): 
    if (type(date) == tuple) & (date.__len__() == 3):
        year = yyyy2yy(date[0])
        month = m2mm(date[1])
        week = day2week(date[2])
        date_convert = "{}{}w{}".format(year, month, week)
        return date_convert
    else:
        pass

def move_folders_zotero(goodnote, zotero): # move goodnote files to target and zotero folder
    for annotated_pdf_route in goodnote:
        pdf_name = annotated_pdf_route.split("/")[-1]
        try:
            zotero_root = zotero[pdf_name] + "/"
            os.remove(zotero_root + pdf_name)
            copyfile(annotated_pdf_route, zotero_root + pdf_name)
        except:
            pass

def move_folders_target(goodnote, target):
    for annotated_pdf_route in goodnote:
        pdf_name = annotated_pdf_route.split("/")[-1]
        src_name = target + annotated_pdf_route.split("/")[-2] + "/"
        if os.path.exists(src_name + pdf_name):
            try:
                os.remove(src_name + pdf_name)
                copyfile(annotated_pdf_route, src_name + pdf_name)                
            except:
                pass

def myprint(script):
    script_len = len(script)
    lines = "=" * script_len
    print(lines)
    print(script)
    print(lines)

def append_rule(var, dictionary, file):
    if var in dictionary.keys():
        try:
            idx = dictionary[var].index(file)
            return "exists"
        except ValueError: # new element
            return "new"
    else:
        return "new_key"

if __name__ == "__main__":
    FileManager()
