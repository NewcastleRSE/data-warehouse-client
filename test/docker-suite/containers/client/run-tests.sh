exec 3>&1 1>outputs/tests.log 2>&1

echo "Starting tests" 1>&3

python3 -m unittest -v -b tests.connection 1>&3
