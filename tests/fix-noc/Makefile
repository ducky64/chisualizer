#=======================================================================
# UCB Chisel Flow: Makefile 
#-----------------------------------------------------------------------
# Brian Zimmer (bmzimmer@eecs.berkeley.edu)
#
# This makefile will generate verilog files or an emulator from chisel code
CSRC_DIR = $(abspath emulator)

RTL_FILES := Makefile ../../../flo/src/main/scala/*.scala

CPP_FILES = $(CSRC_DIR)/FixNetwork2d.cpp $(CSRC_DIR)/main.cpp
OBJ_FILES = $(CPP_FILES:.cpp=.o)
INCLUDES = $(wildcard $(CSRC_DIR)/*.h)

LDFLAGS = -g
CPPFLAGS = -g -O2 -I$(CSRC_DIR) -I$(CSRC_DIR)
CPP = g++

PROGFILE := $(CSRC_DIR)/emulator

default: emulator

$(CSRC_DIR)/%.cpp: $(RTL_FILES)
	cd ../../../flo && sbt -mem 16384 "project flo" "run new-fix-grid --rows 2 --cols 2 --ports grid --array grid --portsDump $(CSRC_DIR)/network.conn --backend c --targetDir $(CSRC_DIR) --debug --ioDebug"

$(CSRC_DIR)/%.o: $(CSRC_DIR)/%.cpp $(INCLUDES)
	$(CPP) $(CPPFLAGS) -c -o $@ $<

$(CSRC_DIR)/main.o: main.cpp $(INCLUDES)
	$(CPP) $(CPPFLAGS) -c -o $@ $<

$(PROGFILE): $(OBJ_FILES)
	$(CPP) $(LDFLAGS) -o $@ $^

emulator: $(PROGFILE) 

run: emulator
	python ../../src/main.py  --emulator emulator/emulator --visualizer_desc fix-noc.yaml

clean:
	rm -rf emulator project target
