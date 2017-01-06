
.ONESHELL:

target: report_pdf

report_pdf: report_images
	cd report
	pdflatex measure_academic_dishonesty.tex
	cd ..

report_images:
	python3 src/reporting.py

pylint:
	pylint src/*.py | grep -v I:  > log

tests:
	python src/tests.py