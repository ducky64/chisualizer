#=======================================================================
# UCB Chisel Flow: Makefile 
#-----------------------------------------------------------------------
# Brian Zimmer (bmzimmer@eecs.berkeley.edu)
#
# This makefile will generate verilog files or an emulator from chisel code


src_files := Makefile src/main/scala/*.scala
emulator_timestamp    := emulator/generated-src/timestamp

compile:
	sbt "project main" compile

$(emulator_timestamp): $(src_files)
	sbt "project main" "run --backend c --targetDir emulator/generated-src"
	date > $(emulator_timestamp)

emulator: $(emulator_timestamp)

run-emulator: emulator
	cd emulator; make run

clean:
	rm -rf emulator/generated-src/* main target

