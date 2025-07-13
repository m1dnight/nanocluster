
# JMeter

Jmeter is installed on all the nodes. Start it locally with
`/opt/jmeter/start.sh` and stop it again with `/opt/jmeter/stop.sh`

For testing, run an nginx or something on your machine
```shell
docker run -it --rm -p 80:80 nginx
```

To start all the machines

```shell
ansible -i hosts all -a "/opt/jmeter/start.sh" --become
```

To stop all the machines

```shell
ansible -i hosts all -a "/opt/jmeter/stop.sh" --become
```


On your machine, start the JMeter client with

```shell
jmeter -t roles/jmeter/files/CallCC.jmx -Djava.rmi.server.hostname="<client ip>" -J server.rmi.ssl.disable=true
```