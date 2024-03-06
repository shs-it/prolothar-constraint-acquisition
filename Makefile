build_fast_downward:
	cd thirdparties/fast-downward && python build.py || cd ../..

build_metric_ff:
	cd thirdparties/metric-ff/v1.0 && make || cd ../../..

clean_metric_ff:
	cd thirdparties/metric-ff/v1.0 && make clean || cd ../../..

build_metric_ff2:
	cd thirdparties/metric-ff/v2.1 && make || cd ../../..

clean_metric_ff2:
	cd thirdparties/metric-ff/v2.1 && make clean || cd ../../..

build_planminer:
	cd thirdparties/PlanMiner && cmake . && make && cd ../../..

build_planminer_wsl:
	cd thirdparties/PlanMiner && wsl cmake . && wsl make && cd ../../..

cython :
	python setup.py build_ext --inplace

clean :
	python setup.py clean --all

test :
	python -m coverage erase
	python -m coverage run --branch --source=./prolothar_ca -m unittest discover -v
	python -m coverage xml -i
