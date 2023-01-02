for i in *.wav; do
  name=${i%.*}
  echo $name
  sox "$i" -r 11050 "$name-low.wav"
done