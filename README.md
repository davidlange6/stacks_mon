
## Run
```
./stacks_mon -n <label> <executable> <arguments>
```

will monitor your process with minimal performacne loss and produce 

```memory_<label>.log``` : Subprocess level rss and vsiz reports and event number if your log has "Begin event action" inside

```selftimes_<label>_<procid>.out```: Subprocess level stacks ordered according to how much time is spent in each top level function

```callstackinfo_<label>_<procid>.out```: Subprocess level statistics on call stacks appropriate to use with flamegraph tools 
(eg ```cat callstackinfo.out | ./flamegraph.pl > flamegraph.png```)

## Dependencies
Depends on https://github.com/fantasyzh/uniqstack (including the path to libunwind suggested there)
