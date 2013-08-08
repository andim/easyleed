
RM = /bin/rm -f
TEMPFILES = easyleed/*.pyc

clean:
	$(RM) $(TEMPFILES)

zip:
	find . -name "*.py" | zip ../doc/source/_static/source.zip -@
