#!/usr/bin/perl -W

use warnings;
use strict;
use POSIX;
use Time::Piece;
use Time::Seconds;

local $/ = '</tr>';
open(WGET, 'wget -qO - https://www.hanza.net/cgi-bin/hanzanet?pageId=hanzanet.investor.funds.allFunds |');

my $summa = 80020;
my $kogus = 831;
my $kontohooldus = 10;
my $algus = Time::Piece->strptime("01-02-2004", "%d-%m-%Y"); #14-02-2004
my $praegu = localtime;
my $kuid = do { $algus = $praegu - $algus; ceil($algus->months) };

my @val = ();
my $vaartus = 0;
my $kasum = 0;
my $hooldustasu = 0;

STOP: while(<WGET>) {
	if (/HLF:HAM/) { 
		@val = (split "</td>")[2,3,4,5,6];
		map {
			s/\s*<td[^>]*>//;
			s/.*value="([^"]*)".*/$1/;
		} @val;
		#map { s/.*(;|")([-0-9.]{3,}).*/$2/ } @val;
		last STOP;
	}
}

close(WGET);

#printf "Kuupäev: %s, \nmuutus: %.2f%%, väärtus: %.2f
printf "Kuupäev: %s, \nmuutus: %s, väärtus: %.2f
ost: %.2f, myyk: %.2f.
Hetke myygihind: %.2f 

Kasum: %.2f
Kontohooldustasu: %.2f
",
$val[0], $val[1], $val[2], 
$val[3], $val[4],
($vaartus=$kogus*$val[4]),
($kasum=$vaartus-$summa),
($hooldustasu=$kuid*$kontohooldus);

$kasum > 0 
	and printf "Puhaskasum (-tulumaks ja hooldus): %.2f\n", ($kasum*0.74)-$hooldustasu;
