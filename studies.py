# List of URLs to scrape
urls = list(set([
    "https://www.hgha.com/testosterone-levels-in-men-by-age/",
    "https://my.clevelandclinic.org/health/articles/24101-testosterone",
    "https://www.medicalnewstoday.com/articles/323085",
    "https://www.endocrine.org/news-and-advocacy/news-room/2017/landmark-study-defines-normal-ranges-for-testosterone-levels",
    "https://www.urmc.rochester.edu/encyclopedia/content.aspx?contenttypeid=167&contentid=testosterone_total",
    "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4190174/",
    "https://www.ncbi.nlm.nih.gov/books/NBK532933/",
    "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7520594/",
    "https://www.merckmanuals.com/professional/genitourinary-disorders/male-reproductive-endocrinology-and-related-disorders/male-hypogonadism",
    "https://journals.lww.com/tnpj/Fulltext/2017/02000/Approaches_to_male_hypogonadism_in_primary_care.8.aspx",
    "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4336035/",
    "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3955331/",
    "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4546699/",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0010",
    "https://endocrinenews.endocrine.org/the-long-haul-treating-men-with-obesity-with-testosterone/",
    "https://www.uptodate.com/contents/7460",
    "https://www.webmd.com/a-to-z-guides/what-is-sex-hormone-binding-globulin",
    "https://www.healthline.com/health/low-shbg",
    "https://journals.lww.com/tnpj/fulltext/2024/08000/testosterone_replacement_therapy_for_hypogonadism_.6.aspx",
    "https://journals.lww.com/tnpj/abstract/2012/08000/testosterone_replacement_therapy_to_improve_health.11.aspx",
    "https://journals.lww.com/tnpj/citation/2024/08000/testosterone_replacement_therapy_for_hypogonadism_.7.aspx",
    "https://journals.lww.com/tnpj/fulltext/2017/02000/approaches_to_male_hypogonadism_in_primary_care.8.aspx",
    "https://journals.lww.com/tnpj/abstract/2016/08000/evaluation_and_treatment_of_male_hypogonadism_in.10.aspx",
    "https://journals.lww.com/tnpj/fulltext/2018/11000/diabetic_autonomic_neuropathy_resulting_in_sexual.7.aspx",
    "https://journals.lww.com/tnpj/fulltext/2020/05000/infertility_management_in_primary_care.11.aspx",
    "https://journals.lww.com/tnpj/fulltext/2010/12000/male_infertility__a_primer_for_nps.9.aspx",
    "https://journals.lww.com/tnpj/citation/2009/09000/testosterone_replacement_therapy__what_to_look.12.aspx",
    "https://journals.lww.com/tnpj/abstract/1991/09000/the_effect_of_drugs_on_male_sexual_function_and.9.aspx",
    "https://journals.lww.com/tnpj/abstract/2003/07000/is_bio_identical_hormone_therapy_fact_or_fairy.8.aspx",
    "https://journals.lww.com/tnpj/citation/2006/09000/erectile_dysfunction.9.aspx",
    "https://journals.lww.com/tnpj/citation/2014/05000/evaluation_of_a_scrotal_mass.3.aspx",
    "https://journals.lww.com/tnpj/citation/2004/12000/erectile_dysfunction_in_primary_care.6.aspx",
    "https://www.webmd.com/men/news/20230616/cm/testosterone-safe-for-most-older-men",
    "https://www.webmd.com/erectile-dysfunction/erectile-dysfunction",
    "https://www.webmd.com/men/xyosted-low-testosterone",
    "https://www.webmd.com/men/features/keep-testosterone-in-balance",
    "https://www.webmd.com/men/features/infertility",
    "https://www.webmd.com/men/features/testosterone-therapy-safety",
    "https://www.webmd.com/erectile-dysfunction/testosterone-replacement-therapy",
    "https://www.webmd.com/men/how-low-testosterone-can-affect-your-sex-drive",
    "https://www.webmd.com/men/what-low-testosterone-can-mean-your-health",
    "https://www.webmd.com/men/features/testosterone-therapy-pros-cons",
    "https://www.webmd.com/men/testosterone-replacement-therapy-is-it-right-for-you",
    "https://www.webmd.com/men/replacement-therapy",
    "https://www.liebertpub.com/doi/10.1089/andro.2022.0009",
    "https://www.liebertpub.com/doi/10.1089/andro.2022.0007",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0027",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0003",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0013",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0026",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0034",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0001",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0025",
    "https://www.liebertpub.com/doi/10.1089/andro.2022.0011",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0001",
    "https://www.liebertpub.com/doi/10.1089/andro.2022.0020",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0028",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0007",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0023",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0018",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0015",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0018",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0011",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0008",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0030",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0024",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0009",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0019",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0019",
    "https://www.liebertpub.com/doi/10.1089/andro.2022.0004",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0033",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0013",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0010",
    "https://www.liebertpub.com/doi/10.1089/andro.2022.0005",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0031",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0006",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0035",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0029",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0016",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0002",
    "https://www.liebertpub.com/doi/10.1089/andro.2022.0012",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0003",
    "https://www.liebertpub.com/doi/10.1089/andro.2022.0010",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0032",
    "https://www.liebertpub.com/doi/10.1089/andro.2020.0012",
    "https://www.liebertpub.com/doi/10.1089/andro.2022.0021",
    "https://www.liebertpub.com/doi/10.1089/andro.2022.29008.editorial",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0010",
    "https://www.liebertpub.com/doi/10.1089/andro.2022.29007.editorial",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0006",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0015",
    "https://www.liebertpub.com/doi/10.1089/andro.2021.0014",
    "https://www.liebertpub.com/doi/10.1089/andro.2022.0003",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC6391653/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC8998588/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC10438885/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC9901191/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC10884082/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC6287281/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC10296187/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC9472648/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC8087565/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC10335606/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC7025895/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC7689919/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC5858094/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC9415930/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC11151480/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC6462402/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC8649267/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC7591257/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC7328342/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC8994707/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC9006970/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC9510302/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC9016457/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC8596965/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC6503299/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC11355538/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC9484057/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC5858095/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC10890669/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC8603719/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC10425362/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC11298165/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC6944317/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC10919420/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC7060639/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC6014638/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC8548546/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC10355707/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC10477232/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC7304096/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC7993603/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC5392926/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC7271464/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC8166567/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC6252085/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC10851319/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC6436191/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC6583468/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC10619376/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC9270305/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC5698762/",
    "https://www.merckmanuals.com/professional/special-subjects/illicit-drugs-and-intoxicants/anabolic-steroids?query=testosterone",
    "https://www.merckmanuals.com/professional/genitourinary-disorders/male-reproductive-endocrinology-and-related-disorders/male-reproductive-endocrinology?query=testosterone",
    "https://www.merckmanuals.com/professional/endocrine-and-metabolic-disorders/pituitary-disorders/selective-pituitary-hormone-deficiencies?query=testosterone",
    "https://www.merckmanuals.com/professional/genitourinary-disorders/male-reproductive-endocrinology-and-related-disorders/gynecomastia?query=testosterone",
    "https://www.merckmanuals.com/professional/endocrine-and-metabolic-disorders/adrenal-disorders/overview-of-adrenal-function?query=testosterone",
    "https://www.merckmanuals.com/professional/pediatrics/congenital-renal-and-genitourinary-anomalies/penile-anomalies?query=testosterone",
    "https://www.urmc.rochester.edu/conditions-and-treatments/testosterone-deficiency-syndrome",
    "https://my.clevelandclinic.org/podcasts/cardiac-consult/testosterone-replacement-therapy-in-patients-with-low-testosterone-findings-from-traverse-trial",
    "https://my.clevelandclinic.org/podcasts/love-your-heart/is-testosterone-replacement-therapy-safe-for-your-heart"
]))
