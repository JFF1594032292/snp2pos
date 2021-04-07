# snp2pos
Annotate SNPs rs id to pos and allele in a more convenient and flexible way.
If we want to search some SNPs pos and allele information in dbSNP from rs-id, grep is a time-consuming way. Usually we build a dict for whole genome SNPs, but it's also consume memory and time.The tabix is quick, however it can only search snp-id from pos.
So I utilized the tabix to write a small tool to search snp information in a big file (>15G, db154 vcf format file). Overall, it run as fast as tabix (~200 SNP/s), and i's convenient to combine with other command in shell pipe.
