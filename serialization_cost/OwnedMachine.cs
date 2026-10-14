// Complete benign finite-table interpreter. No network, device or OS state control.
// The program exposes observations only; its identity is fixed for the process.
using System;
using System.Diagnostics;
using System.Globalization;
using System.IO;

public static class OwnedMachine {
    private static void Need(bool ok, string text) {
        if (!ok) throw new InvalidDataException(text);
    }
    public static int Main(string[] args) {
        var clock=Stopwatch.StartNew();
        try {
            Need(args.Length==3,"table path, identity and reset budget required");
            int identity=Int32.Parse(args[1],CultureInfo.InvariantCulture);
            int budget=Int32.Parse(args[2],CultureInfo.InvariantCulture);
            Need(budget>=-1 && budget<=12,"budget domain");
            var raw=File.ReadAllText(args[0]);
            var fields=raw.Split((char[])null,StringSplitOptions.RemoveEmptyEntries);
            Need(fields.Length<=20000,"owned table bound");
            int cursor=0;
            Func<int> take=()=>Int32.Parse(fields[cursor++],CultureInfo.InvariantCulture);
            int n=take(), actions=take();
            Need(n>=1 && n<=24 && actions==2 && identity>=0 && identity<n,"dimensions");
            int initial=0, count=0; int[,] output=null, target=null;
            for (int h=0; h<n; h++) {
                int states=take(), start=take();
                Need(states>=1 && states<=16 && start>=0 && start<states,"state domain");
                var oo=new int[states,actions]; var tt=new int[states,actions];
                for (int s=0; s<states; s++) for (int a=0; a<actions; a++) {
                    oo[s,a]=take(); tt[s,a]=take();
                    Need(oo[s,a]>=0 && oo[s,a]<=1 && tt[s,a]>=0 && tt[s,a]<states,"edge domain");
                }
                if (h==identity) {initial=start; count=states; output=oo; target=tt;}
            }
            Need(cursor==fields.Length && output!=null && count>0,"complete table");
            int state=initial, steps=0, resets=0;
            Console.WriteLine("READY clr="+Environment.Version+" stopwatch_frequency="+Stopwatch.Frequency+" high_resolution="+Stopwatch.IsHighResolution);
            string line;
            while ((line=Console.ReadLine())!=null) {
                if (line=="stop") {
                    using (var p=Process.GetCurrentProcess()) {
                        Console.WriteLine("END steps="+steps+" resets="+resets+" cpu_ticks="+p.TotalProcessorTime.Ticks+" peak_working_set_bytes="+p.PeakWorkingSet64+" worker_wall_ticks="+clock.ElapsedTicks);
                    }
                    return 0;
                }
                int action=Int32.Parse(line,CultureInfo.InvariantCulture);
                Need(steps<64 && action>=0 && action<=actions,"owned step bound");
                int observed;
                if (action==actions) {
                    Need(budget!=0,"reset budget exhausted");
                    if (budget>0) budget--;
                    state=initial; observed=0; resets++;
                } else {observed=output[state,action]; state=target[state,action];}
                steps++;
                Console.WriteLine("OBS "+observed);
            }
            throw new InvalidDataException("missing stop");
        } catch (Exception ex) {
            Console.Error.WriteLine(ex.GetType().Name+": "+ex.Message);
            return 1;
        }
    }
}
