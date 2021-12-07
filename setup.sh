echo "---- Jmmith Setup ----"
echo "This script helps set up Jmmith. It uses Maximilian's setup script, then does a few extra steps."
echo "Cloning Maximilian..."
echo ""
if [ -d maximilian ]
then
    echo "It looks like Maximilian was already cloned. Pulling changes...
    cd maximilian
    git pull
    cd ..
else
    git clone https://github.com/tk421bsod/maximilian
fi
echo ""
echo "Running Maximilian's setup.sh... Follow the prompts it gives you."
echo ""
cd maximilian
sleep 1
bash setup.sh
echo ""
if [ $? != 0 ]
then
    echo "Maximilian's setup exited unexpectedly. Try running this again."
    exit 37
fi
echo "Moving some Maximilian components here..."
cd ..
cp maximilian/common.py .
cp maximilian/errorhandling.py .
cp maximilian/dbp.txt .
cp maximilian/token.txt .
cp maximilian/helpcommand.py .
cp maximilian/core.py .
cp maximilian/errors.py .
echo "Finishing database setup..."
sudo mysql maximilian -Be "CREATE TABLE jmmboard(message_id bigint); CREATE TABLE draobmmj(message_id bigint); CREATE TABLE jmmboardconfig(guild_id bigint, setting text, enabled tinyint);"
echo "Cleaning up..."
rm -rf maximilian
echo "Done. Try running main.py. If you want Jmmith to work in threads, install discord.py 2.0 (instructions are at https://github.com/rapptz/discord.py/blob/master/README.rst)"
