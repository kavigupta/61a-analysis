
.ONESHELL:

target: report_pdf

report_pdf: report_images
	cd report
	pdflatex measure_academic_dishonesty.tex
	cd ..

report_images:
	mkdir report/img
	python3 src/reporting.py
	touch report_images

pylint:
	pylint src/*.py | grep -v I:  > log

tests:
	python src/tests.py

clean:
	rm report_images
	rm report/measure_academic_dishonesty.pdf
	rm report/img/*

profile:
	mv -f prof.log prof-bak.log
	python -O -u -m cProfile -s cumtime src/profile.py --plausible-params > prof.log
