#!/bin/bash
cd /home/claude/reenact
for s in S1 S3 S5 S8; do
  bvenv/bin/python scene.py $s --scale 70 --samples 10 --out render/$s > logs_$s.txt 2>&1
  grep RENDERED logs_$s.txt >> render_progress.txt
done
echo ALLDONE >> render_progress.txt
