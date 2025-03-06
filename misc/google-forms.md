# Google Forms

read the source code.

No seriously, pretty much all the information about a google form is sitting there. 
There were two Google Form related challenges at LA CTF 2024. The first one involved a inputting the flag with each character as a separate question, leading to a final page that says correct or incorrect. The second one involved a one question open-response quiz that looped on itself.

## How Google Forms Work
The entire structure of the form is in any given page's source code, if you're willing to map it out. Stored in json objects, every question and answer option is listed along with a number of factors (often defaulted to null), including the pages it directs the user to. For quizzes it is even simpler, because the answers are stored in the same arrays. 

Because the first challenge used a dropdown format, where every option except for the first sent the user to a different (although identical) page than the correct option. We could solved the first challenge by looking at every option and the page numbers they direct to. Every option except for the correct one had the same one, whereas the correct one would be different. From there we could map out the path to the end, and derive the flag. 
The second challenge is much easier, and solves every quiz format Google Form. You just look in the source code and Ctrl+F the flag.  

There are many lists of many attributes and values stored in the source code, but the question and answers will look like this:
Apologies for the language:
```
[[367298180,"1. fuck",null,3,[[1512361774,[["me",null,-2,null,0],["in",null,-3,null,0],["the",null,-3,null,0],["ass",null,-3,null,0],["hole",null,-3,null,0]],1,null,null,null,null,null,0]],null,null,null,null,null,null,[null,"1. fuck"]],
```
The larger array refers to the section, titled `"1. fuck"` with the number `367298180`. The question number is `1512361774`. I don't know what every factor refers to but, there is than an array of answer options. The first option is the visible answer (`"me"`), with third option referring to the page it leads to (`-2`). The `-3` option means the submit page, whereas `-2` refers to another section. In the challenge, all page numbers were longer (like `556692759`), but the last question featured `-2` for the incorrect answers (leading to another section), and -3 for the last correct answer.

## More 
Among all the google analytics mining your forms for data, there is a single POST request that includes all the important information. 
```
POST /forms/d/e/1FAIpQLSc-A-Vmx_Te-bAqnu3TrRj-DAsYTgn52uSk92v3fECQb3T83A/formResponse HTTP/2
Host: docs.google.com
Cookie: S=spreadsheet_forms=ZGVfEpEoZ_cU_tA0UwzTm51Lmu6v9lkcCRNCAonrbGA; COMPASS=spreadsheet_forms=CjIACWuJV1PCDN_YaKhS38kyvsTFoyeM-VDV2IQNjC6UdTd2bNQ5TUkPy3U6iPYWvtWVeBCjgcGuBhpDAAlriVfNzJKNCqTdoOAC_94gRQe249BWzrxdtMTUZjUC1qsFJDfw2bUnUCUL3zVc7Q4RZE0FVAdDs6Wz5A1Eoy4WlQ==; NID=511=OwtdOb3KPkOGqSdnksGNGb-jchNpZF8qHveglNTcD5aRFyWVxXUQrbg5lCbiG1Mv7lFPARrd3y1RkHurJT1Wa1hy7iMWrUP272YOtJSF-NbMxhR4mGDmEM_UH7nkGFmFvwxgQv-ZbAeYc1C-TBf7dbGVftm-EM7BJsDKUwvSF8I
Content-Length: 299
Cache-Control: max-age=0
Sec-Ch-Ua: 
Sec-Ch-Ua-Mobile: ?0
Sec-Ch-Ua-Platform: ""
Upgrade-Insecure-Requests: 1
Origin: https://docs.google.com
Content-Type: application/x-www-form-urlencoded
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.111 Safari/537.36
Accept: text/html,application/xhtml xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
X-Client-Data: CNOIywE=
Sec-Fetch-Site: same-origin
Sec-Fetch-Mode: navigate
Sec-Fetch-User: ?1
Sec-Fetch-Dest: document
Referer: https://docs.google.com/forms/d/e/1FAIpQLSc-A-Vmx_Te-bAqnu3TrRj-DAsYTgn52uSk92v3fECQb3T83A/formResponse
Accept-Encoding: gzip, deflate
Accept-Language: en-US,en;q=0.9

entry.1377469227=5&fvv=1&partialResponse=[[[null,853714080,["batman's kitchen"],0],[null,561191505,["a"],0],[null,267419203,["8"],0]],null,"2396555994171379564"]&pageHistory=0,2,3,5&fbzx=2396555994171379564&continue=1
```

The first field includes the entry for a given question, this form only had one question per page, but presumably there might be more if there were more questions on the page. The partial response includes a list of all of the previous page numbers and and the chosen answers. The page history parameter includes the pages visited, it can be manipulated without needing to put in feasible path (it may give problems, but seems to be fine as long as the page exists). Why forms appears to use both a long random generated integer and a linear sequential reference to track pages I do not know. I also do not know what `fvv` and `fbzx` refer to. 

Best I can tell, neither the requests nor responses leak the Google Sheets it sends information too. 

In short, Google Forms are not secure and Google should have never introduced a quiz function. Don't transmit passwords in Google Forms. 
