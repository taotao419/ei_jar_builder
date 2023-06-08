#!/usr/bin/python
from git import *
import configparser
import os
import shutil

JAR_MAP = {
    "agility-ris-server/server/com.agfa.agility.model.core": "lib",
    "agility-ris-server/server/com.agfa.ris.server.web": "server",
    "agility-ris-server/server/com.agfa.ris.server.reporting": "server",
    "agility-ris-server/server/com.agfa.ris.server": "server",
    "agility-ris-server/server/com.agfa.agility.fhir.r4.service": "server",
    "agility-ris-server/common/com.agfa.ris.server.common.rendertemplates": "lib",
    "agility-ris-server/server/com.agfa.ris.server.api": "lib",
    "agility-ris/client/com.agfa.ris.client.genericsearch.integration": "client",
}

SOURCE_MODIFY_TIME = {

}

EI_MONOREPO_PATH="D:\AGFA-Code-EI-monorepo\ei-monorepo"


def get_changed_jar_paths():
    repo = Repo(EI_MONOREPO_PATH)
    jar_set = set()
    for item in repo.index.diff(None):
        print("[INFO] Changed File : {}".format(item.a_path))
        pos = item.a_path.find('/src/main')
        if pos != -1:
            jar_path = item.a_path[:pos]
            jar_set.add(jar_path)
            source_path = EI_MONOREPO_PATH+"\\{}".format(
                item.a_path)
            source_modify_time = os.stat(source_path).st_mtime
            if SOURCE_MODIFY_TIME.get(jar_path, 0) < source_modify_time:
                SOURCE_MODIFY_TIME[jar_path] = source_modify_time
    return jar_set

# only return source code file modify time greater than jar modify time
def skip_latest_jar(jar_set):
    result = set()
    for jar in jar_set:
        last_splash_pos = jar.rfind('/')
        jar_name = jar[last_splash_pos+1:]
        jar_path = EI_MONOREPO_PATH+"\{}\\build\\libs\\{}-100.0.0.SNAPSHOT.jar".format(
            jar, jar_name)
        jar_modify_time = os.stat(jar_path).st_mtime
        if SOURCE_MODIFY_TIME[jar] > jar_modify_time:
            result.add(jar)
            print("[INFO] The Latest Jar : {} , source mtime {} , jar mtime {} ".format(jar,SOURCE_MODIFY_TIME[jar], jar_modify_time))
        else:
            print("\033[32m[INFO] The Latest Jar : {} , No more building \033[0m".format(jar))
    return result


def build_jar(jar_set):
    os.chdir(EI_MONOREPO_PATH)
    for jar_path in jar_set:
        clean_cmd = "call .\gradlew :{}:clean".format(jar_path.replace('/', ':'))
        build_cmd = "call .\gradlew :{}:jar".format(jar_path.replace('/', ':'))
        print("[INFO] Building Jar : {}".format(jar_path.replace('/', ':')))
        os.system(clean_cmd)
        os.system(build_cmd)


def copy_jar(jar_set):
    print(jar_set)
    for jar in jar_set:
        last_splash_pos = jar.rfind('/')
        jar_name = jar[last_splash_pos+1:]
        mode = JAR_MAP.get(jar)
        source_path = EI_MONOREPO_PATH+"\{}\\build\\libs\\{}-100.0.0.SNAPSHOT.jar".format(
            jar, jar_name)
        target_path = ""
        if mode == "server":
            target_path = EI_MONOREPO_PATH+"\\agility-install\\server\\jboss\\standalone\\deployments\\agility.ear\\{}.jar".format(
                jar_name)
        elif mode == "lib":
            target_path = EI_MONOREPO_PATH+"\\agility-install\\server\\jboss\\standalone\\deployments\\agility.ear\\lib\\{}.jar".format(
                jar_name)
        elif mode == "client":
            target_path = EI_MONOREPO_PATH+"\\agility-install\server\jboss\standalone\deployments\webstart.war\plugins\{}_100.0.0.SNAPSHOT.jar".format(
                jar_name)
        else:
            print("\033[31m[ERROR] Unknown jar [{}] , please update JAR_MAP CONST \033[0m".format(
                jar_name))
        if os.path.isfile(target_path) == False:
            print("\033[31m[ERROR] File Not Existed  [{}] , please check it \033[0m".format(
                target_path))

        if target_path != "":
            shutil.copy(source_path, target_path)
            print("[copy] {} ==> {}".format(source_path, target_path))


if __name__ == '__main__':
    changed_jars = get_changed_jar_paths()
    filter_jars = skip_latest_jar(changed_jars)
    build_jar(filter_jars)
    copy_jar(filter_jars)
    os.system("taskkill /F /IM EnterpriseImagingJBoss.exe")
