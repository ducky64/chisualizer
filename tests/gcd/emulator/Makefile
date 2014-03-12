SRC_DIR = ./generated-src
LDFLAGS = -g
CPPFLAGS = -g -O2 -I$(SRC_DIR)
CPP = g++
CPP_FILES = $(SRC_DIR)/GCD.cpp main.cpp
# CPP_FILES = $(wildcard $(SRC_DIR)/*.cpp)
OBJ_FILES = $(CPP_FILES:.cpp=.o)
# INCLUDES = $(SRC_DIR)/emulator.h $(SRC_DIR)/GCD.h
INCLUDES = $(wildcard $(SRC_DIR)/*.h)

default : all

$(SRC_DIR)/%.o: $(SRC_DIR)/%.cpp $(INCLUDES)
	$(CPP) $(CPPFLAGS) -c -o $@ $<

GCD-emulator: $(OBJ_FILES)
	$(CPP) $(LDFLAGS) -o $@ $^

run : GCD-emulator
	./GCD-emulator

all : GCD-emulator

clean :
	rm $(SRC_DIR)/*.o *.o GCD-emulator

