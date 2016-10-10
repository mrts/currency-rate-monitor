#!/bin/bash

# 
# Skript dollari kursi muutusest ülevaate saamiseks ja
# mingi dollarikoguse hetkeväärtuse arvutamiseks.
# Dollari kurss küsitakse Ühispangast.
#
# Kasutamine: dollarikurss.sh [--help]
#   --help  väljastab pikema abiteksti

. "$0.conf" || { echo "$0.conf: ei õnnestu avada" >&2; exit; }

# FUNKTSIOONID
#-----------------------------------------------------

die() { echo -e "$0: $*" >&2; exit 1; }
msg() { echo -e "$0: $*"; }

kasutus()
{
	msg \
	"Skript dollari kursi muutusest ülevaate saamiseks ja\n"\
	"mingi dollarikoguse hetkeväärtuse arvutamiseks.\n"\
	"Dollari kurss küsitakse Ühispangast.\n\n"\
        "Kasutamine: $0 [--help]\n"\
	"  --help  väljastab käesoleva abiteksti"
}

# Kontrollib, kas konfiguratsioon OK
kontrolli_muutujaid()
{
        for i in $wget $sed $gawk $cat $bc
        do
                [ -x "$i" ] \
			|| die "$i: programm pole kasutatav,"\
                               "palun määra konfiguratsioonifailis uus asukoht."
        done
	[ -w $arhiiv ] || > $arhiiv \
		|| die "$arhiiv: ei saa faili kirjutada"
}

# Laeb Ühispanga veebist uue dollari kursi
kysi_uus_kurss()
{
	uus_kurss=( `$wget -qO - 'http://www.eyp.ee/pages.php3/012103'\
		     | $gawk -F'[><]' -v ORS=' ' \
			'/USA dollar.*lekande ost/ { print $3 };\
			 /USA dollar - Eesti Panga/ { print $3 }' | tr , .` )

	[ ${#uus_kurss[*]} -eq 2 ] \
		|| die "kursi küsimine Ühispangast ebaõnnestus."
}

# Laeb arhiivifailist vanad kursid ja salvestab sinna uue
lae_vanad_ja_salvesta_uus_kurss()
{
	local len

	vanad_kursid=( $(< $arhiiv) )

	echo ${uus_kurss[*]} >| $arhiiv

	if (( ${#vanad_kursid} == 0 ))
	then 
		msg "arhiivifail oli tühi"
		vanad_kursid=( ${uus_kurss[*]} )
	else
		len=$(( ${#vanad_kursid[*]} < 18 ? ${#vanad_kursid[*]} : 18 ))
		for (( i=0; i < len; i++ ))
		do
			if (( i % 2 )) 
			then
				echo ${vanad_kursid[$i]} >> $arhiiv
			else 
				echo -n "${vanad_kursid[$i]} " >> $arhiiv
			fi
		done
	fi
}

# Väljastab vara väärtuse muutuse ja kursimuutuse
v2ljasta_kursivahe()
{
	tulemus=(`echo  "${uus_kurss[0]}-${vanad_kursid[0]};"\
			"${uus_kurss[1]}-${vanad_kursid[1]};"\
			"$kogus*${uus_kurss[0]};"\
			"$kogus*${uus_kurss[0]}-$kogus*$algne_kurss" | $bc`)

	cat <<EOT

Soetuskurss:     $algne_kurss
----------------------------------------
                 EYP arve ost   EP
Tänane kurss:    ${uus_kurss[0]}	${uus_kurss[1]}
Kursimuutus:     ${tulemus[0]}	${tulemus[1]}
----------------------------------------
Hetkeväärtus:    ${tulemus[2]}
Väärtuse muutus: ${tulemus[3]}


EOT
}

# ABIFUNKTSIOON: prindib graafiku ühe tulba
dotprint(){
	local mitu=$1 

	echo -n '|'
	for (( j=0; j <= mitu/2; j++ ))
	do
		echo -n '_'
	done
	(( mitu % 2 )) && echo -n '.'
}

# ABIFUNKTSIOON: prindib graafiku alla skaala
skaalaprint()
{
	local algus=$1 
	local mantiss=$((algus - (algus/100)*100))
	local max=$((mantiss+101))

	echo "|+----+----+----+----+----+----+----+----+----+----+"
	while (( mantiss < max ))
	do
		if (( mantiss > 99 ))
		then
			echo -n " ${mantiss:1}  "
		else
			printf " %.2d  " $mantiss
		fi
		(( mantiss += 10 )) 
	done
	echo -e "\n $((algus/100)).                     "\
		"$(((algus+50)/100)).                      $(((algus+100)/100))."
	echo -e "\nÜks ühik skaalal = 0,02 EEK. Punkt: paaritu väärtus."
}

# Väljastab dollari kursi muutuse graafiku
v2ljasta_kursigraafik()
{
	local kurss kesk algus 

	echo -e "Eesti Panga kursi muutus (uuemad kursid ülalpool):\n"

	kesk=`echo "n=(${uus_kurss[1]}*100)/1; n + n%2" | $bc`
	algus=$(( kesk - 50 ))

	# saaks lihtsamalt
	dotprint `echo "(${uus_kurss[1]}*100)/1 - $algus" | $bc`
	echo "  (${uus_kurss[1]})"

	for (( i=1; i < ${#vanad_kursid[*]}; i+=2 ))
	do
		# võimalus optimeerida: à la AB-päringud -- esmalt
		# tsüklis valmistatakse päringud ette (ühte massiivi),
		# siis ühekordse bc väljakutsumisega arvutatakse väärtus
		kurss=`echo "(${vanad_kursid[$i]}*100)/1 - $algus" | $bc`
		(( kurss < 0 || kurss > 100 )) \
			&& die "kurss ${vanad_kursid[$i]} jääb skaalast väljapoole. Krahh?"
		dotprint $kurss
		echo 
	done
	skaalaprint $algus
}

# SKRIPT ISE
#-----------------------------------------------------

(( $# == 0 )) || { kasutus; exit 1; }

declare -a uus_kurss
declare -a vanad_kursid
declare -a tulemus

kontrolli_muutujaid
kysi_uus_kurss
lae_vanad_ja_salvesta_uus_kurss
v2ljasta_kursivahe
v2ljasta_kursigraafik
