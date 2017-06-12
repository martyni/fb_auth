source env/bin/activate
zappa update $1 | tee build.log
awk -F "live!:" /amazonaws.com/'{print $2}' build.log > url

for file in $(ls app/static/)
	do s3_static martyni-static auth $1 app/static/$file
done	

if [ -z $(cat url) ] 
    then
    zappa deploy $1 | tee build.log
    awk -F "complete!:" /amazonaws.com/'{print $2}' build.log > url
fi    
