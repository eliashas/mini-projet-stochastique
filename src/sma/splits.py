def temporal_folds(df):
    years = df.valid_time.dt.year
    for name, end, lo, hi in [('F1',1970,1971,1980),('F2',1980,1981,1990),('F3',1990,1991,2000)]:
        train = df.loc[(years>=1940)&(years<=end)].copy()
        val = df.loc[(years>=lo)&(years<=hi)].copy()
        assert len(train)==end-1940+1 and len(val)==10
        assert train.valid_time.max()<val.valid_time.min()
        yield name,train,val
