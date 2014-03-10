LDFLAGS = -g
CPPFLAGS = -g -O2 -I./generated-src
CPP = g++
INCLUDES = generated-src/emulator.h generated-src/GCD.h

default : all

GCD.o: generated-src/GCD.cpp $(INCLUDES)
	$(CPP) $(CPPFLAGS) -c $<

GCD-emulator.o: testbench/GCD-emulator.cpp $(INCLUDES)
	$(CPP) $(CPPFLAGS) -c $<

GCD-emulator: GCD-emulator.o GCD.o
	$(CPP) $(LDFLAGS) -o $@ $+

run : GCD-emulator
	./GCD-emulator

all : GCD-emulator

clean :
	rm GCD-emulator.o GCD.o GCD-emulator
