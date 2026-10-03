<?php

function buildCharacterMap($jsonFile, $language): array
{
    if (!file_exists($jsonFile)) {
        return [];
    }

    $data = json_decode(
        file_get_contents($jsonFile),
        true
    );

    if (!is_array($data)) {
        return [];
    }

    $characterSheet = null;
    $localizeSheet = null;

    // Find Character and Localize sheets
    $findSheets = function ($data) use (
        &$findSheets,
        &$characterSheet,
        &$localizeSheet
    ) {
        if (!is_array($data)) {
            return;
        }

        if (isset($data['name'], $data['rows'])) {

            if (
                str_ends_with(
                    $data['name'],
                    ':Character'
                )
            ) {
                $characterSheet = $data;
            }

            if (
                str_ends_with(
                    $data['name'],
                    ':Localize'
                )
            ) {
                $localizeSheet = $data;
            }
        }

        foreach ($data as $value) {
            if (is_array($value)) {
                $findSheets($value);
            }
        }
    };

    $findSheets($data);

    if (!$characterSheet) {
        return [];
    }

    $characterNames = [];

    foreach ($characterSheet['rows'] ?? [] as $row) {

        $strings = $row['strings'] ?? [];

        $key = trim($strings[0] ?? '');
        $name = trim($strings[1] ?? '');

        if ($key !== '' && $name !== '') {
            $characterNames[$key] = $name;
        }
    }

    // If there is no localization sheet,
    // return the common names directly.
    if (!$localizeSheet) {
        return $characterNames;
    }

    /*
     * Find language column.
     */
    $headers = [];

    foreach ($localizeSheet['rows'] ?? [] as $row) {

        if (($row['rowIndex'] ?? -1) == 0) {
            $headers = $row['strings'] ?? [];
            break;
        }
    }

    $languageColumn = array_search(
        $language,
        $headers,
        true
    );

    if ($languageColumn === false) {
        return $characterNames;
    }

    $localizedNames = [];

    foreach ($localizeSheet['rows'] ?? [] as $row) {

        $strings = $row['strings'] ?? [];

        $commonName = trim($strings[0] ?? '');

        if ($commonName === '') {
            continue;
        }

        $translation = trim(
            $strings[$languageColumn] ?? ''
        );

        if ($translation !== '') {
            $localizedNames[$commonName] = $translation;
        }
    }

    /*
     * Final lookup:
     *
     * character ID → translated name
     */
    $characterMap = [];

    foreach ($characterNames as $key => $commonName) {

        $characterMap[$key] =
            $localizedNames[$commonName]
            ?? $commonName;
    }

    return $characterMap;
}


function normalize_lookup_text($text): string {
    return mb_convert_kana($text, 'n', 'UTF-8');
}
function format_rich_text($text): string
{
    // Convert literal line breaks
    $text = str_replace(
        ["\\n", "\r\n", "\n", "\r"],
        "<br>",
        $text
    );

    // Escape HTML
    $text = htmlspecialchars(
        $text,
        ENT_QUOTES,
        'UTF-8'
    );

    // Restore only tags we explicitly allow
    $text = str_replace(
        [
            '&lt;ruby&gt;',
            '&lt;/ruby&gt;',
            '&lt;rt&gt;',
            '&lt;/rt&gt;',
            '&lt;rp&gt;',
            '&lt;/rp&gt;',
            '&lt;br&gt;'
        ],
        [
            '<ruby>',
            '</ruby>',
            '<rt>',
            '</rt>',
            '<rp>',
            '</rp>',
            '<br>'
        ],
        $text
    );

    return $text;
}


function parse_story_to_html($json, $selectedLang): string {
    $jsonFile = __DIR__ . '/repo_b/json/common.chapter.json';
    $characterMap = buildCharacterMap($jsonFile,$selectedLang);
    $playerName = trim($_POST['playerName'] ?? '');

    $data = json_decode($json, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        return "<div class='error'>Invalid JSON: " . htmlspecialchars(json_last_error_msg()) . "</div>";
    }
    
    if (empty($data['m_Structure']['importGridList'])&&empty($data['importGridList'])) {
        return "<div class='error'>Missing important structure!</div>";
    }
  
    // 🔍 Auto-detect language column index dynamically
$languageIndex = "Japanese"; // default fallback
$firstGrid = $data['m_Structure']['importGridList'][0] 
    ?? $data['importGridList'][0];



$header = $firstGrid['rows'][0]['strings'] ?? [];
$headerMap = array_flip($header);

// Detect Voice column
$voiceIndex = null;
if (isset($headerMap['Voice'])) {
    $voiceIndex = $headerMap['Voice'];
}


if (isset($headerMap[$selectedLang])) {
    $languageIndex = $headerMap[$selectedLang];
}

//Test run

// Load JSON file 2
$translationMap = [];

$translationFile = __DIR__ . '/translation.json';

if (file_exists($translationFile)) {

    $translationData = json_decode(
        file_get_contents($translationFile),
        true
    );

    if (json_last_error() === JSON_ERROR_NONE) {

        $translationRows = $translationData['rows'] ?? [];

        // JSON file 2 header
        $translationHeader =
            $translationRows[0]['strings'] ?? [];

        $translationHeaderMap =
            array_flip($translationHeader);

        // Find columns dynamically
        $spriteIndex =
            $translationHeaderMap['Sprite'] ?? null;
                                
        $translationIndex =
            $translationHeaderMap[$selectedLang] ?? null;

        if (
            $spriteIndex !== null &&
            $translationIndex !== null
        ) {

            foreach ($translationRows as $translationRow) {

                $rowStrings =
                    $translationRow['strings'] ?? [];

                if (
                    isset($rowStrings[$spriteIndex]) &&
                    isset($rowStrings[$translationIndex])
                ) {

                    $key =normalize_lookup_text(
                        trim($rowStrings[$spriteIndex]));

                    if ($key !== '') {

                        $translationMap[$key] =
                            $rowStrings[$translationIndex];

                    }
                }
            }
        }
    }
}

//Test end
    $html = "<ol>\n";
    foreach ($data['m_Structure']['importGridList'] ?? $data['importGridList'] as $grid) {
        $rawName = $grid['name'] ?? 'Unnamed';
    // Extract substring after '.xls:'
    if (strpos($rawName, '.xls:') !== false) {
        $parts = explode('.xls:', $rawName);
        $rawName = $parts[1];
    }

    $shortName = preg_match('/\*?(quest_[A-Za-z0-9_\-]+)/', $rawName, $matches) ? $matches[1] : $rawName;
    $name = htmlspecialchars($shortName);
    $html .= "<li><a href='#$name'>$name</a></li>\n";
}
    $html .= "</ol>\n";

    foreach ($data['m_Structure']['importGridList'] ?? $data['importGridList'] as $grid) {
        $rawGridName = $grid['name'] ?? 'Unnamed';
        if (strpos($rawGridName, '.xls:') !== false) {
    $parts = explode('.xls:', $rawGridName);
    $rawGridName = $parts[1];
}
        $shortGridName = preg_match('/quest_[A-Za-z0-9_\-]+/', $rawGridName, $matches) ? $matches[0] : $rawGridName;
        $gridName = htmlspecialchars($shortGridName);
        $html .= "<h3 id='$gridName'>$gridName</h3>\n";

            //Test
            $windowTypeIndex = null;

            if (!empty($grid['rows'][0]['strings'])) {
                $gridHeader = $grid['rows'][0]['strings'];
                $gridHeaderMap = array_flip($gridHeader);
                $windowTypeIndex = $gridHeaderMap['WindowType'] ?? null;
            }
            $theaterMode = false;
            $echoMode = false;
            
            //Test end
        foreach ($grid['rows'] ?? [] as $row) {

            if (!empty($row['isEmpty']) || !empty($row['isCommentOut']) || ($row['rowIndex'] === 0)) continue;

            $strings = $row['strings'] ?? [];
            if (empty($strings)) continue;
          
// Track WindowType
if ($windowTypeIndex !== null) {
    $windowType = trim($strings[$windowTypeIndex] ?? '');

    if ($windowType === 'MessageWindow_theater') {
        $theaterMode = true;
        $echoMode = false;
    } elseif ($windowType === 'MessageWindowEcho') {
        $theaterMode = false;
        $echoMode = true;
    } elseif ($windowType === 'MessageWindow') {
        $theaterMode = false;
        $echoMode = false;
    }
}
            $cmd = trim($strings[0] ?? '');

            if (str_starts_with($cmd, '*')) {
                $label = htmlspecialchars(ltrim($cmd, '*'));
                $html .= "<div class='label' id='$label'>Label: $label</div>\n";
            }
//Last understand
if ($cmd === "Selection") {
    $cond = trim($strings[3] ?? '');
    $text = $strings[$languageIndex] ?? '[No Text]';
    //$text = str_replace(['\\u003c', '\\u003e'], ['<', '>'], $text);
if ($cond !== '') {
    $text .= " [Set {$cond}]";
}
/*
if ($playerName !== '') {
    $text = str_replace(
        ['<param=playerName>', '<param=pronounTradChineseName1>', '<param=pronounTradChineseName2>', '<param=teamLeaderCharaName>'],
        $playerName,
        $text
    );
}*/

/*
    // Process ruby tags
    $text = preg_replace_callback('/<ruby=(.*?)>(.*?)<\/ruby>/', function ($matches) {
        $rt = htmlspecialchars($matches[1], ENT_QUOTES, 'UTF-8');
        $rb = htmlspecialchars($matches[2], ENT_QUOTES, 'UTF-8');
        return "<ruby>{$rb}<rp>(</rp><rt>{$rt}</rt><rp>)</rp></ruby>";
    }, $text);

    // Process emphasis tags
    $text = preg_replace_callback('/<em=(.*?)>(.*?)<\/em>/', function ($matches) {
        $mark = str_replace('.', '・', $matches[1]);
        $mark = htmlspecialchars($mark, ENT_QUOTES, 'UTF-8');
        $content = htmlspecialchars($matches[2], ENT_QUOTES, 'UTF-8');
        $chars = preg_split('//u', $content, -1, PREG_SPLIT_NO_EMPTY);
        $result = '';
        foreach ($chars as $char) {
            $result .= "<ruby>{$char}<rt>{$mark}</rt></ruby>";
        }
        return $result;
    }, $text);

    // Strip <speed> tags
    //$text = preg_replace(['/<speed=([\d.]+)>/', '/<\/speed>/'], '', $text);

    // Escape entire text first
    // Protect <param=...> tags from being stripped
$text = preg_replace('/<param=([^>]+)>/', '&lt;param=\1&gt;', $text);


    // Restore ruby-related tags
    $text = str_replace(
        ['&lt;br&gt;', '&lt;ruby&gt;', '&lt;/ruby&gt;', '&lt;rt&gt;', '&lt;/rt&gt;', '&lt;rp&gt;', '&lt;/rp&gt;'],
        ['<br>', '<ruby>', '</ruby>', '<rt>', '</rt>', '<rp>', '</rp>'],
        $text
    );
*/
    // Restore <span style="font-size">
$text = preg_replace_callback('/<size=(\d+)>(.*?)<\/size>/s', function ($matches) {
    $originalSize = intval($matches[1]);
    $adjustedSize = max(5, $originalSize - 15);
    $content = $matches[2];
    return "<span style=\"font-size:{$adjustedSize}px\">{$content}</span>";
}, $text);

    // Line breaks
    if($selectedLang=="English"){
    $text = str_replace(["\\n", "\r\n", "\n", "\r"], "<br> ", $text);
}else{
$text = str_replace(["\\n", "\r\n", "\n", "\r"], "<br>", $text);
}
    $condition = trim($strings[2] ?? '');
    $label = htmlspecialchars(ltrim($strings[1] ?? '', '*'));
    
    
        // Output HTML
    if (!empty($condition)) {
        $html .= "<div class='select'><a href='#$label'>$text</a> <span class='cond'>( If: " . htmlspecialchars($condition) . " )</span></div>\n";
    } else {
        $html .= "<div class='select'><a href='#$label'>$text</a></div>\n";
    }

            } elseif ($cmd === "Label") {
                $label = htmlspecialchars(ltrim($strings[1] ?? '', '*'));
                $html .= "<div class='label' id='$label'>Label: $label</div>\n";
            } elseif ($cmd === "Jump") {
 $dest = htmlspecialchars(ltrim($strings[1] ?? '', '*'));
    $condition = trim($strings[2] ?? '');

    // If there is a condition, display it inside brackets
    if (!empty($condition)) {
        $html .= "<div class='jump'>Jump to <a href='#$dest'>$dest</a> <span class='cond'>( If: " . htmlspecialchars($condition) . " )</span></div>\n";
    } else {
        $html .= "<div class='jump'>Jump to <a href='#$dest'>$dest</a></div>\n";
    }
    } elseif ($cmd === "Bg") {
        $originalText = normalize_lookup_text(trim($strings[1] ?? ''));
        if ($originalText !== '' && isset($translationMap[$originalText])) 
        {
            // Found in JSON file 2
            $translatedText = format_rich_text($translationMap[$originalText]);
            $html .= "<p>Title: {$translatedText}</p>\n";
        } else {
            // Not found in JSON file 2
            $text = htmlspecialchars($originalText);
            $html .= "<p>Background: {$text}</p>\n";
        }

            }elseif ($cmd === "Param") {
                $text = htmlspecialchars($strings[1] ?? '');
                $html .= "<p>Set: $text</p>\n";
            }elseif ($cmd === "Bgm") {
                $text = htmlspecialchars($strings[1] ?? '');
                $html .= "<p>BGM: $text</p>\n";
            }elseif ($cmd === "TitleImage"){
		$text1 = htmlspecialchars($strings[1] ?? '');
                $text2 = htmlspecialchars($strings[2] ?? '');
                $html .= "<p>Title: $text1- $text2</p>\n";
            }elseif ($cmd === "Sprite") {
    $originalText = normalize_lookup_text(trim($strings[1] ?? ''));
    if (
        $originalText !== '' &&
        isset($translationMap[$originalText])
    ) {
        // Found in JSON file 2
        $translatedText = htmlspecialchars($translationMap[$originalText]);
        // Convert \n from JSON into an HTML line break
        $translatedText = str_replace(
            ["\\n", "\r\n", "\n", "\r"],
            "<br>",
            $translatedText
        );
        $html .= "<p>Title: {$translatedText}</p>\n";
    }
            }elseif(in_array($cmd, ['Wait', 'If','EndIf','Se','SendMessage','Shake','StopSe','Tween','FadeOut','BgOff','ZoomCamera','FadeIn','ImageEffect','ImageEffectOff','RuleFadeOut','RuleFadeIn','CaptureImage','SpriteOff','VideoEffect','Timeline','Particle'], true)){
                continue;
		} else {
                $chara = trim($strings[1] ?? '');
                $emotion = trim($strings[2] ?? '');
                $text = trim($strings[$languageIndex] ?? '');
                
            if ($chara !== '') {
                $chara = $characterMap[$chara] ?? $chara;
            }
                //if (!empty($text)) {
                    $text = str_replace(['\\u003c', '\\u003e'], ['<', '>'], $text);
if ($playerName !== '') {
    $text = str_replace(
        ['<param=playerName>', '<param=pronounTradChineseName1>', '<param=pronounTradChineseName2>', '<param=teamLeaderCharaName>'],
        $playerName,
        $text
    );
}

                    $text = preg_replace_callback('/<ruby=(.*?)>(.*?)<\/ruby>/', function ($matches) {
                        $rt = htmlspecialchars($matches[1], ENT_QUOTES, 'UTF-8');
                        $rb = htmlspecialchars($matches[2], ENT_QUOTES, 'UTF-8');
                        return "<ruby>{$rb}<rp>(</rp><rt>{$rt}</rt><rp>)</rp></ruby>";
                    }, $text);

                    $text = preg_replace_callback('/<em=(.*?)>(.*?)<\/em>/', function ($matches) {
                        $mark = str_replace('.', '・', $matches[1]);
     $mark = htmlspecialchars($mark, ENT_QUOTES, 'UTF-8');
    $content = htmlspecialchars($matches[2], ENT_QUOTES, 'UTF-8');
    $chars = preg_split('//u', $content, -1, PREG_SPLIT_NO_EMPTY);
    $result = '';
    foreach ($chars as $char) {
        $result .= "<ruby>{$char}<rt>{$mark}</rt></ruby>";
    }
    return $result;
}, $text);

                    
// Remove <speed=...> and </speed> tags
$text = preg_replace(['/<speed=([\d.]+)>/', '/<\/speed>/'], '', $text);
// Replace <size=...>...</size> with <span style="font-size:...px">...</span>
$text = preg_replace_callback('/<size=(\d+)>(.*?)<\/size>/s', function ($matches) {
    $originalSize = intval($matches[1]);
    $adjustedSize = max(1, $originalSize - 15);
    $content = $matches[2];
    return "<span style=\"font-size:{$adjustedSize}px\">{$content}</span>";
}, $text);

// Escape HTML first
// Protect <param=...> tags from being stripped
$text = preg_replace('/<param=([^>]+)>/', '&lt;param=\1&gt;', $text);



// Restore allowed tags like <br>, <ruby>, etc.
$text = str_replace(
    ['&lt;br&gt;', '&lt;ruby&gt;', '&lt;/ruby&gt;', '&lt;rt&gt;', '&lt;/rt&gt;', '&lt;rp&gt;', '&lt;/rp&gt;'],
    ['<br>', '<ruby>', '</ruby>', '<rt>', '</rt>', '<rp>', '</rp>'],
    $text
);

// Restore <span style="font-size:...px"> by parsing <size=...> inside already-escaped text
$text = preg_replace_callback('/&lt;size=(\d+)&gt;(.*?)&lt;\/size&gt;/s', function ($matches) {
    $originalSize = intval($matches[1]);
    $adjustedSize = max(5, $originalSize - 15); // avoid zero or negative size
    $content = $matches[2];
    return "<span style=\"font-size:{$adjustedSize}px\">{$content}</span>";
}, $text);


                    $text = str_replace(
                        ['&lt;br&gt;', '&lt;ruby&gt;', '&lt;/ruby&gt;', '&lt;rt&gt;', '&lt;/rt&gt;', '&lt;rp&gt;', '&lt;/rp&gt;'],
                        ['<br>', '<ruby>', '</ruby>', '<rt>', '</rt>', '<rp>', '</rp>'],
                        $text
                    );

                    if($selectedLang == "English"){
                    $text = str_replace(["\\n", "\r\n", "\n", "\r"], "<br> ", $text);
}else{
$text = str_replace(["\\n", "\r\n", "\n", "\r"], "<br>", $text);
}

$voice = ($voiceIndex !== null) ? trim($strings[$voiceIndex] ?? '') : "";


// Prepare voice HTML (gray, in brackets)
$voiceTag = "";
if (!empty($voice)) {
    $voiceEscaped = htmlspecialchars($voice, ENT_QUOTES, 'UTF-8');
    $voiceTag = " <span class='voice'>[{$voiceEscaped}]</span>";
}
if ($chara === '' && $text === '') {
    continue;
}

if (!empty($chara)) {

    // Keep the original speaker from the uploaded JSON
    $originalChara = trim($strings[1] ?? '');
    $originalEmotion = trim($strings[2] ?? '');

    // $chara has already been localized above
    $localizedChara = $characterMap[$originalChara] ?? $originalChara;
    $localizedLabel = $localizedChara;
    $originalLabel = $originalChara;
    if ($originalEmotion !== '') {
        $originalLabel .= " ($originalEmotion)";
    }
    $localizedEscaped = htmlspecialchars($localizedLabel,ENT_QUOTES,'UTF-8');
    $originalEscaped = htmlspecialchars($originalLabel,ENT_QUOTES,'UTF-8');
    $textClass = $theaterMode? 'text theater': ($echoMode ? 'text echo' : 'text');
    $textClass .= ($text === '' ? ' character-only' : '');
    $html .=
        "<div class='$textClass'>" .
        "<span class='chara' " .
        "data-localized='" . $localizedEscaped . "' " .
        "data-original='" . $originalEscaped . "'>" .
        $localizedEscaped .
        ":</span> " .
        "$text$voiceTag" .
        "</div>\n";

} else {

                        $textClass = $theaterMode ? 'text narration theater' : ($echoMode ? 'text narration echo' : 'text narration');
                        $html .= "<div class='$textClass'>$text$voiceTag</div>\n";

                    }
                //}
            }
        }
    }

    return $html;
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Parsed Story</title>
<style>
h3 {
  top: 0;
  position: sticky;
  background: #7986CB;
  padding: 5px;
}
.select {
  background: #8888ff;
  color: #fff;
}
.select a {
  color: #fff !important;
  text-decoration: none;
}
.select .cond {
  color: #fff;

}
.jump {
  background: #88ff88;
}
.label {
  background: #ffff88;
}
.label:target {
  background: #ff8888;
}
.chara {
  font-weight: 900;
}
.text {
  background: #f0f0f0;
}
.title {
  background: #88ffff;
}
.voice {
  color: #7f7f7f;
}
.select, .jump, .label, .text, textarea, .title {
  margin: 10px;
  padding: 10px;
}
.cond-block {
  margin-inline-start: 2px;
  margin-inline-end: 2px;
  padding-block-start: 0.35em;
  padding-inline-start: 0.75em;
  padding-inline-end: 0.75em;
  padding-block-end: 0.625em;
  min-inline-size: min-content;
  border: 2px groove threedface;
}
.cond {
  padding-inline-start: 2px;
  padding-inline-end: 2px;
  border-width: initial;
  border-style: none;
  border-color: initial;
  border-image: initial;
}
.effect {
  padding: 5px;
  line-height: 2;
  white-space: nowrap;
  border-radius: 5px;
  background: #888888;
  color: #fff;
}
em {
  text-emphasis: circle;
  -webkit-text-emphasis: circle;
  font-style: normal;
}
#storyContainer.hide-br br {
  display: none;
}
.hide-ruby rt {
  display: none;
}
.hide-ruby ruby {
text-shadow: 0 0 8px #ee00ee;
  background: #ffaaff;
}
.control {
  position: fixed;
  top: 15px;
  right: 10px;
  background: #fff;
}
.text.theater {
  background: #ffeded;
}
.text.echo {
  background: #dddddd;
}
#storyContainer.hide-character-only .character-only {
  display: none;
}

</style>
</head>
<body>

<fieldset class="control">
<legend>Control</legend>
<input type="checkbox" id="br-btn"><label for="br-btn">Hide line break</label><br>
<input type="checkbox" id="ruby-btn"><label for="ruby-btn">Hide ruby text</label><br>
<input type="checkbox" id="character-only-btn" checked><label for="character-only-btn">Hide character-only</label><br>
<input type="checkbox" id="original-speaker-btn"><label for="original-speaker-btn">Show original speaker</label><br>
<button type="button" onclick="window.history.back()" style="margin-top:5px;">🔙 Back</button>
</fieldset>


<h2>📖 Parsed Story</h2>
<button id="saveHtmlBtn" style="margin: 10px; padding: 8px 15px;">💾 Save as HTML</button>

<div id=storyContainer>
<?php
if ($_SERVER['REQUEST_METHOD'] === 'POST') {

    // Check if a file was uploaded
    if (isset($_FILES['jsonFile']) && $_FILES['jsonFile']['error'] === UPLOAD_ERR_OK) {
        $fileTmpPath = $_FILES['jsonFile']['tmp_name'];
        $jsonContent = file_get_contents($fileTmpPath);

        // Optional: decode JSON to verify it's valid
        $data = json_decode($jsonContent, true);
        if (json_last_error() !== JSON_ERROR_NONE) {
            die("Invalid JSON file.");
        }

        // Get other form inputs
        $language = $_POST['language'] ?? '';
echo parse_story_to_html($jsonContent, $language);

    } else {
        echo "No file uploaded or upload error.";
    }
} else {
    echo "Invalid request method.";
}
?>
</div>

<script>
document.querySelector("#br-btn").onclick = function() {
  document.getElementById("storyContainer").classList.toggle("hide-br");
};
document.querySelector("#ruby-btn").onclick = function() {
  document.body.classList.toggle("hide-ruby");
};


// Character-only: ON by default
const characterOnlyBtn = document.querySelector("#character-only-btn");

function updateCharacterOnly() {
    document
        .getElementById("storyContainer")
        .classList.toggle(
            "hide-character-only",
            characterOnlyBtn.checked
        );
}

updateCharacterOnly();

characterOnlyBtn.addEventListener("change", updateCharacterOnly);


// Original speaker
document.querySelector("#original-speaker-btn").addEventListener("change", function () {

    const useOriginal = this.checked;

    document.querySelectorAll(".chara").forEach(function (speaker) {

        const value = useOriginal
            ? speaker.dataset.original
            : speaker.dataset.localized;

        speaker.textContent = value + ":";
    });

});

// Save current page content as a standalone HTML file
document.getElementById("saveHtmlBtn").addEventListener("click", function () {
    const fullHtml =
        "<!DOCTYPE html>\n<html>\n" +
        document.documentElement.innerHTML +
        "\n</html>";

    const blob = new Blob([fullHtml], { type: "text/html" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = "story_output.html";
    link.click();

    URL.revokeObjectURL(url);
});

</script>


</body>
</html>
