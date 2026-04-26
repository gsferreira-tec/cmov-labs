# Redirect OLSR Network - notes

- Packet 256 is the 1st solicitation from h4 to h2 in the capture, before h4 only solicited h3 and
vice-versa.

- The immediate ICMPv6 packet does not find a response with the 
full 64 hops as hop limi

- 1st Redirect Packert is @ 259 

- Redirect packets continue until

[1776687865.556740] 64 bytes from 2029::1: icmp_seq=215 ttl=63 time=0.172 ms
[1776687888.085617] 64 bytes from 2029::1: icmp_seq=237 ttl=63 time=0.883 ms
[1776687889.086279] 64 bytes from 2029::1: icmp_seq=238 ttl=63 time=0.200 ms  9:
