#=======================================================================
# UCB Chisel Flow: Makefile 
#-----------------------------------------------------------------------
# Brian Zimmer (bmzimmer@eecs.berkeley.edu)
#
# This makefile will generate verilog files or an emulator from chisel code
CSRC_DIR = emulator
GSRC_DIR = emulator/generated-src

RTL_FILES := Makefile src/main/scala/*.scala
RTL_TIMESTAMP := $(GSRC_DIR)/timestamp

CPP_FILES = $(GSRC_DIR)/GCD.cpp emulator/main.cpp
OBJ_FILES = $(CPP_FILES:.cpp=.o)
INCLUDES = $(wildcard $(GSRC_DIR)/*.h)

LDFLAGS = -g
CPPFLAGS = -g -O2 -I$(CSRC_DIR) -I$(GSRC_DIR)
CPP = g++

PROGFILE := $(CSRC_DIR)/emulator

default: emulator

#$(RTL_TIMESTAMP): $(RTL_FILES)
#	sbt "project main" "run --backend c --targetDir $(GSRC_DIR)"
#	date > $(RTL_TIMESTAMP)

#csrc: $(RTL_TIMESTAMP)
#$(GSRC_DIR)/%.cpp: $(RTL_TIMESTAMP)

$(GSRC_DIR)/%.cpp: $(RTL_FILES)
	sbt "project main" "run --backend c --targetDir $(GSRC_DIR)"

$(CSRC_DIR)/%.o: $(CSRC_DIR)/%.cpp $(INCLUDES)
	$(CPP) $(CPPFLAGS) -c -o $@ $<

$(GSRC_DIR)/%.o: $(GSRC_DIR)/%.cpp $(INCLUDES)
	$(CPP) $(CPPFLAGS) -c -o $@ $<

$(PROGFILE): $(OBJ_FILES)
	$(CPP) $(LDFLAGS) -o $@ $^

emulator: $(PROGFILE) 

clean:
	rm -rf emulator/generated-src/* main target

