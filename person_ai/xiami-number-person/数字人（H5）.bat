@echo off
title %~dp0
cls
color 0A
echo ====================================================================================================
echo Running path	%~dp0
echo Running 1.	java -jar -Dserver.port=[PORT] -Dserver.servlet.context-path=[/PATH] [NAME].jar
echo Running 2.	java -jar -Dspring.config.location=[PATH/application.yml] [NAME].jar
echo ====================================================================================================
cd /d %~dp0
java -jar web-digital-human.jar
pause
@echo on