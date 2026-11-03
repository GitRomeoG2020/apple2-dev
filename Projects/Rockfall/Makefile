# Box build (Linux). On Windows use build.ps1.
BIN=/workspace/apple2/bin
all: disk/rockfall.dsk
build/rockfall.bin: src/rockfall.s src/sprites.s src/rockfall.cfg
	cd src && $(BIN)/ca65 rockfall.s -o ../build/rockfall.o -l ../build/rockfall.lst
	$(BIN)/ld65 -C src/rockfall.cfg build/rockfall.o -o $@ -m build/rockfall.map
disk/rockfall.dsk: build/rockfall.bin tools/mkdisk.py
	python3 tools/mkdisk.py $< $@
clean:
	rm -f build/* disk/*
