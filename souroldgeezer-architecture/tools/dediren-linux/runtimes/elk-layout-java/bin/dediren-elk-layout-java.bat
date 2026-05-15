@rem
@rem Copyright 2015 the original author or authors.
@rem
@rem Licensed under the Apache License, Version 2.0 (the "License");
@rem you may not use this file except in compliance with the License.
@rem You may obtain a copy of the License at
@rem
@rem      https://www.apache.org/licenses/LICENSE-2.0
@rem
@rem Unless required by applicable law or agreed to in writing, software
@rem distributed under the License is distributed on an "AS IS" BASIS,
@rem WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
@rem See the License for the specific language governing permissions and
@rem limitations under the License.
@rem
@rem SPDX-License-Identifier: Apache-2.0
@rem

@if "%DEBUG%"=="" @echo off
@rem ##########################################################################
@rem
@rem  dediren-elk-layout-java startup script for Windows
@rem
@rem ##########################################################################

@rem Set local scope for the variables, and ensure extensions are enabled
setlocal EnableExtensions

set DIRNAME=%~dp0
if "%DIRNAME%"=="" set DIRNAME=.
@rem This is normally unused
set APP_BASE_NAME=%~n0
set APP_HOME=%DIRNAME%..

@rem Resolve any "." and ".." in APP_HOME to make it shorter.
for %%i in ("%APP_HOME%") do set APP_HOME=%%~fi

@rem Add default JVM options here. You can also use JAVA_OPTS and DEDIREN_ELK_LAYOUT_JAVA_OPTS to pass JVM options to this script.
set DEFAULT_JVM_OPTS="-XX:-UsePerfData"

@rem Find java.exe
if defined JAVA_HOME goto findJavaFromJavaHome

set JAVA_EXE=java.exe
%JAVA_EXE% -version >NUL 2>&1
if %ERRORLEVEL% equ 0 goto execute

echo. 1>&2
echo ERROR: JAVA_HOME is not set and no 'java' command could be found in your PATH. 1>&2
echo. 1>&2
echo Please set the JAVA_HOME variable in your environment to match the 1>&2
echo location of your Java installation. 1>&2

"%COMSPEC%" /c exit 1

:findJavaFromJavaHome
set JAVA_HOME=%JAVA_HOME:"=%
set JAVA_EXE=%JAVA_HOME%/bin/java.exe

if exist "%JAVA_EXE%" goto execute

echo. 1>&2
echo ERROR: JAVA_HOME is set to an invalid directory: %JAVA_HOME% 1>&2
echo. 1>&2
echo Please set the JAVA_HOME variable in your environment to match the 1>&2
echo location of your Java installation. 1>&2

"%COMSPEC%" /c exit 1

:execute
@rem Setup the command line

set CLASSPATH=%APP_HOME%\lib\dediren-elk-layout-java.jar;%APP_HOME%\lib\jackson-annotations-2.17.3.jar;%APP_HOME%\lib\jackson-core-2.17.3.jar;%APP_HOME%\lib\jackson-databind-2.17.3.jar;%APP_HOME%\lib\org.eclipse.elk.alg.layered-0.11.0.jar;%APP_HOME%\lib\org.eclipse.elk.alg.libavoid-0.11.0.jar;%APP_HOME%\lib\org.eclipse.elk.alg.common-0.11.0.jar;%APP_HOME%\lib\org.eclipse.elk.core-0.11.0.jar;%APP_HOME%\lib\org.eclipse.elk.graph-0.11.0.jar;%APP_HOME%\lib\org.eclipse.xtext.xbase.lib-2.32.0.jar;%APP_HOME%\lib\guava-32.1.2-jre.jar;%APP_HOME%\lib\listenablefuture-9999.0-empty-to-avoid-conflict-with-guava.jar;%APP_HOME%\lib\org.eclipse.emf.ecore.xmi-2.12.0.jar;%APP_HOME%\lib\org.eclipse.core.runtime-3.31.0.jar;%APP_HOME%\lib\org.eclipse.core.contenttype-3.9.300.jar;%APP_HOME%\lib\org.eclipse.equinox.app-1.7.0.jar;%APP_HOME%\lib\org.eclipse.equinox.registry-3.12.0.jar;%APP_HOME%\lib\jsr305-3.0.2.jar;%APP_HOME%\lib\org.eclipse.core.jobs-3.15.200.jar;%APP_HOME%\lib\org.eclipse.equinox.preferences-3.11.0.jar;%APP_HOME%\lib\org.osgi.service.prefs-1.1.2.jar;%APP_HOME%\lib\org.eclipse.emf.ecore-2.12.0.jar;%APP_HOME%\lib\org.eclipse.emf.common-2.12.0.jar;%APP_HOME%\lib\checker-qual-3.33.0.jar;%APP_HOME%\lib\org.eclipse.equinox.common-3.19.0.jar;%APP_HOME%\lib\org.eclipse.osgi-3.19.0.jar;%APP_HOME%\lib\failureaccess-1.0.1.jar;%APP_HOME%\lib\error_prone_annotations-2.18.0.jar;%APP_HOME%\lib\osgi.annotation-8.0.1.jar


@rem Execute dediren-elk-layout-java
@rem endlocal doesn't take effect until after the line is parsed and variables are expanded
@rem which allows us to clear the local environment before executing the java command
endlocal & "%JAVA_EXE%" %DEFAULT_JVM_OPTS% %JAVA_OPTS% %DEDIREN_ELK_LAYOUT_JAVA_OPTS%  -classpath "%CLASSPATH%" dev.dediren.elk.Main %* & call :exitWithErrorLevel

:exitWithErrorLevel
@rem Use "%COMSPEC%" /c exit to allow operators to work properly in scripts
"%COMSPEC%" /c exit %ERRORLEVEL%
